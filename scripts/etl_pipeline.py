"""
scripts/etl_pipeline.py

Bluestock Fintech | Mutual Fund Analytics Capstone
Consolidated ETL pipeline: ingest raw CSVs -> validate -> clean -> load to SQLite.

This replaces the earlier data_ingestion.py + day2_cleaning_db.py scripts with
a single, importable, docstring-documented pipeline that run_pipeline.py calls
as one of its stages. Each stage is a standalone function so it can also be
imported and reused independently (e.g. from a notebook).

Run directly:
    python3 scripts/etl_pipeline.py
"""
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
DB_PATH = BASE_DIR / "data" / "db" / "bluestock_mf.db"

RAW_FILES = [
    "01_fund_master.csv", "02_nav_history.csv", "03_aum_by_fund_house.csv",
    "04_monthly_sip_inflows.csv", "05_category_inflows.csv", "06_industry_folio_count.csv",
    "07_scheme_performance.csv", "08_investor_transactions.csv", "09_portfolio_holdings.csv",
    "10_benchmark_indices.csv",
]


def ingest_and_validate() -> dict:
    """
    Load every raw CSV into memory and run basic sanity checks:
    - every file exists and is readable
    - every amfi_code in fund_master has a matching entry in nav_history

    Returns a dict of {filename: DataFrame} for downstream use.
    """
    datasets = {}
    for filename in RAW_FILES:
        filepath = RAW_DIR / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Expected raw file missing: {filepath}")
        datasets[filename] = pd.read_csv(filepath)

    fund_master = datasets["01_fund_master.csv"]
    nav_history = datasets["02_nav_history.csv"]
    master_codes = set(fund_master["amfi_code"].unique())
    nav_codes = set(nav_history["amfi_code"].unique())
    missing_in_nav = master_codes - nav_codes
    if missing_in_nav:
        raise ValueError(f"{len(missing_in_nav)} amfi_codes in fund_master have no NAV history: {missing_in_nav}")

    return datasets


def clean_nav_history(df_nav: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the NAV history table:
    - parse dates, sort by fund + date
    - reindex each fund to a full business-day range and forward-fill any
      gaps (defensive: avoids silently dropping a fund's data on a day the
      feed missed, without fabricating weekend/holiday rows that would
      distort return-based risk metrics downstream)
    - drop duplicate rows, drop non-positive NAV values
    """
    df_nav = df_nav.copy()
    df_nav["date"] = pd.to_datetime(df_nav["date"])
    df_nav = df_nav.sort_values(["amfi_code", "date"]).drop_duplicates()

    reindexed_parts = []
    for code, group in df_nav.groupby("amfi_code"):
        full_range = pd.bdate_range(group["date"].min(), group["date"].max())
        series = group.set_index("date")["nav"].reindex(full_range).ffill()
        part = series.reset_index().rename(columns={"index": "date"})
        part["amfi_code"] = code
        reindexed_parts.append(part[["amfi_code", "date", "nav"]])

    df_nav_clean = pd.concat(reindexed_parts, ignore_index=True)
    df_nav_clean = df_nav_clean[df_nav_clean["nav"] > 0]
    return df_nav_clean


def clean_investor_transactions(df_trans: pd.DataFrame) -> pd.DataFrame:
    """Standardise transaction type casing, drop invalid amounts/KYC states, parse dates."""
    df_trans = df_trans.copy()
    df_trans["transaction_type"] = df_trans["transaction_type"].str.capitalize()
    df_trans = df_trans[df_trans["amount_inr"] > 0]
    df_trans["transaction_date"] = pd.to_datetime(df_trans["transaction_date"])
    valid_kyc = ["Verified", "Pending", "Rejected"]
    df_trans = df_trans[df_trans["kyc_status"].isin(valid_kyc)]
    return df_trans


def clean_scheme_performance(df_perf: pd.DataFrame) -> pd.DataFrame:
    """Coerce numeric columns and drop rows with an implausible expense ratio."""
    df_perf = df_perf.copy()
    df_perf["expense_ratio_pct"] = pd.to_numeric(df_perf["expense_ratio_pct"], errors="coerce")
    df_perf = df_perf[(df_perf["expense_ratio_pct"] >= 0.1) & (df_perf["expense_ratio_pct"] <= 2.5)]

    for col in ["return_1yr_pct", "return_3yr_pct", "return_5yr_pct"]:
        df_perf[col] = pd.to_numeric(df_perf[col], errors="coerce")

    return df_perf


def load_to_sqlite(df_nav, df_trans, df_perf, df_fund_master) -> None:
    """
    Load the cleaned fact tables plus dim_fund and dim_date into SQLite.

    dim_fund and dim_date are built here rather than left undefined — an
    earlier version of this pipeline only loaded the 3 fact tables even
    though sql/schema.sql defines dim_fund and dim_date, which broke the
    Power BI relationship model until it was patched in Day 5.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{DB_PATH}")

    dim_fund = df_fund_master[
        ["amfi_code", "scheme_name", "fund_house", "category", "sub_category", "risk_category"]
    ].rename(columns={"risk_category": "risk_grade"}).drop_duplicates(subset=["amfi_code"])

    all_dates = pd.concat([df_nav["date"], df_trans["transaction_date"]]).drop_duplicates().sort_values()
    dim_date = pd.DataFrame({"date_id": all_dates.dt.strftime("%Y-%m-%d")})
    dim_date["year"] = pd.to_datetime(dim_date["date_id"]).dt.year
    dim_date["month"] = pd.to_datetime(dim_date["date_id"]).dt.month
    dim_date["day"] = pd.to_datetime(dim_date["date_id"]).dt.day
    dim_date["quarter"] = pd.to_datetime(dim_date["date_id"]).dt.quarter
    dim_date["is_weekend"] = pd.to_datetime(dim_date["date_id"]).dt.dayofweek >= 5
    dim_date = dim_date.reset_index(drop=True)

    tables = {
        "dim_fund": dim_fund,
        "dim_date": dim_date,
        "fact_nav": df_nav,
        "fact_transactions": df_trans,
        "fact_performance": df_perf,
    }
    for name, df in tables.items():
        df.to_sql(name, engine, if_exists="replace", index=False)
        print(f"  loaded {name:20s} {df.shape[0]:>7,} rows")


def run():
    """Run the full ETL pipeline end to end: ingest -> clean -> load."""
    print("Stage 1/3: Ingesting and validating raw CSVs...")
    datasets = ingest_and_validate()
    print(f"  {len(datasets)} raw files loaded and validated OK")

    print("\nStage 2/3: Cleaning...")
    df_nav = clean_nav_history(datasets["02_nav_history.csv"])
    df_trans = clean_investor_transactions(datasets["08_investor_transactions.csv"])
    df_perf = clean_scheme_performance(datasets["07_scheme_performance.csv"])

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df_nav.to_csv(PROCESSED_DIR / "cleaned_nav_history.csv", index=False)
    df_trans.to_csv(PROCESSED_DIR / "cleaned_investor_transactions.csv", index=False)
    df_perf.to_csv(PROCESSED_DIR / "cleaned_scheme_performance.csv", index=False)
    print(f"  cleaned CSVs written to {PROCESSED_DIR}")

    print("\nStage 3/3: Loading into SQLite...")
    load_to_sqlite(df_nav, df_trans, df_perf, datasets["01_fund_master.csv"])
    print(f"  database written to {DB_PATH}")

    print("\nETL pipeline complete.")


if __name__ == "__main__":
    run()

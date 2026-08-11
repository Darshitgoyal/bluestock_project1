"""
Day 5 prep: builds the full 8-table data model that Power BI needs.

Fixes a gap from Day 2: dim_fund and dim_date were defined in sql/schema.sql
but never actually loaded into bluestock_mf.db. This script populates them,
and also loads the remaining industry-level tables (AUM, SIP, category
inflows, folio counts) so the whole model — 8 tables — lives in one SQLite
file AND as clean CSVs (for the "import CSVs directly" fallback path).

Run this once before opening Power BI / Tableau.
"""
import pandas as pd
from sqlalchemy import create_engine
import os

RAW = "data/raw/"
PROC = "data/processed/"
DB_PATH = "sqlite:///bluestock_mf.db"
PBI_DIR = "data_for_powerbi/"

os.makedirs(PBI_DIR, exist_ok=True)


def build_dim_fund():
    print("Building dim_fund...")
    fund_master = pd.read_csv(RAW + "01_fund_master.csv")
    dim_fund = fund_master[[
        "amfi_code", "scheme_name", "fund_house", "category",
        "sub_category", "risk_category"
    ]].rename(columns={"risk_category": "risk_grade"}).drop_duplicates(subset=["amfi_code"])
    return dim_fund


def build_dim_date(nav_df, txn_df):
    print("Building dim_date...")
    all_dates = pd.concat([
        pd.to_datetime(nav_df["date"]),
        pd.to_datetime(txn_df["transaction_date"]),
    ]).drop_duplicates().sort_values()

    dim_date = pd.DataFrame({"date_id": all_dates})
    dim_date["date_id"] = dim_date["date_id"].dt.strftime("%Y-%m-%d")
    dim_date["year"] = pd.to_datetime(dim_date["date_id"]).dt.year
    dim_date["month"] = pd.to_datetime(dim_date["date_id"]).dt.month
    dim_date["day"] = pd.to_datetime(dim_date["date_id"]).dt.day
    dim_date["quarter"] = pd.to_datetime(dim_date["date_id"]).dt.quarter
    dim_date["is_weekend"] = pd.to_datetime(dim_date["date_id"]).dt.dayofweek >= 5
    return dim_date.reset_index(drop=True)


def main():
    engine = create_engine(DB_PATH)

    # --- Existing cleaned fact tables (already correct from Day 2) ---
    fact_nav = pd.read_csv(PROC + "cleaned_nav_history.csv")
    fact_transactions = pd.read_csv(PROC + "cleaned_investor_transactions.csv")
    fact_performance = pd.read_csv(PROC + "cleaned_scheme_performance.csv")

    # --- New: dim_fund, dim_date (fixes Day 2 gap) ---
    dim_fund = build_dim_fund()
    dim_date = build_dim_date(fact_nav, fact_transactions)

    # --- New: industry-level tables for dashboard Pages 1 and 4 ---
    dim_aum_by_fund_house = pd.read_csv(RAW + "03_aum_by_fund_house.csv")
    dim_monthly_sip_inflows = pd.read_csv(RAW + "04_monthly_sip_inflows.csv")
    dim_category_inflows = pd.read_csv(RAW + "05_category_inflows.csv")
    dim_industry_folio_count = pd.read_csv(RAW + "06_industry_folio_count.csv")

    tables = {
        "dim_fund": dim_fund,
        "dim_date": dim_date,
        "fact_nav": fact_nav,
        "fact_transactions": fact_transactions,
        "fact_performance": fact_performance,
        "dim_aum_by_fund_house": dim_aum_by_fund_house,
        "dim_monthly_sip_inflows": dim_monthly_sip_inflows,
        "dim_category_inflows": dim_category_inflows,
    }

    print(f"\nLoading {len(tables)} tables into bluestock_mf.db ...")
    for name, df in tables.items():
        df.to_sql(name, engine, if_exists="replace", index=False)
        print(f"  {name:28s} {df.shape[0]:>7,} rows  x  {df.shape[1]} cols")

    # dim_industry_folio_count kept separate — loaded too, brings total to 8 dashboard tables
    dim_industry_folio_count.to_sql("dim_industry_folio_count", engine, if_exists="replace", index=False)
    print(f"  {'dim_industry_folio_count':28s} {dim_industry_folio_count.shape[0]:>7,} rows  x  {dim_industry_folio_count.shape[1]} cols")

    # --- Also export clean CSVs, for the "import CSVs directly" path ---
    print(f"\nExporting CSVs to {PBI_DIR} ...")
    tables["dim_industry_folio_count"] = dim_industry_folio_count
    for name, df in tables.items():
        out_path = os.path.join(PBI_DIR, f"{name}.csv")
        df.to_csv(out_path, index=False)
        print(f"  {out_path}")

    print("\nDone. 8 tables loaded into bluestock_mf.db and exported as CSVs.")
    print("Tables:", ", ".join(tables.keys()))


if __name__ == "__main__":
    main()

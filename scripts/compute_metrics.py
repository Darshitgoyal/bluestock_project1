"""
scripts/compute_metrics.py

Bluestock Fintech | Mutual Fund Analytics Capstone
Computes CAGR, Sharpe, Sortino, Alpha/Beta, Max Drawdown, and the composite
fund scorecard from cleaned NAV history. This is the importable/scriptable
counterpart to notebooks/04_performance_analytics.ipynb — same formulas,
packaged as reusable functions for run_pipeline.py or other callers.

Note: CAGR is annualised on a 252-trading-day basis (252 / n_trading_days),
not calendar days (days_elapsed / 365.25). Calendar-day annualisation
overstates/understates CAGR depending on how many weekends fall in the
window; trading-day annualisation keeps it consistent with how Sharpe/
Sortino are already annualised elsewhere in this project.

Run directly:
    python3 scripts/compute_metrics.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR = BASE_DIR / "data" / "outputs"

RISK_FREE_RATE = 0.065  # RBI repo rate proxy, annualised


def load_nav_wide():
    """Returns NAV pivoted to (date x amfi_code) and the corresponding daily returns."""
    nav_history = pd.read_csv(PROCESSED_DIR / "cleaned_nav_history.csv", parse_dates=["date"])
    nav_wide = nav_history.pivot(index="date", columns="amfi_code", values="nav").sort_index()
    daily_returns = nav_wide.pct_change().dropna(how="all")
    return nav_wide, daily_returns


def compute_cagr(nav_wide: pd.DataFrame) -> pd.DataFrame:
    """1yr / 3yr / 5yr CAGR per fund, annualised on a 252-trading-day basis."""
    def _cagr(nav_series, years):
        nav_series = nav_series.dropna()
        end_date = nav_series.index.max()
        start_date = end_date - pd.DateOffset(years=years)
        window = nav_series[nav_series.index >= start_date]
        n_trading_days = len(window)
        if n_trading_days < 2:
            return np.nan
        nav_start, nav_end = window.iloc[0], window.iloc[-1]
        if nav_start <= 0:
            return np.nan
        return (nav_end / nav_start) ** (252 / n_trading_days) - 1

    rows = []
    for code in nav_wide.columns:
        series = nav_wide[code]
        rows.append({
            "amfi_code": code,
            "cagr_1yr": _cagr(series, 1),
            "cagr_3yr": _cagr(series, 3),
            "cagr_5yr": _cagr(series, 5),
        })
    return pd.DataFrame(rows)


def compute_sharpe(daily_returns: pd.DataFrame) -> pd.DataFrame:
    """Annualised Sharpe ratio per fund: (mean excess return / std) * sqrt(252)."""
    rf_daily = RISK_FREE_RATE / 252
    rows = []
    for code in daily_returns.columns:
        r = daily_returns[code].dropna()
        excess = r - rf_daily
        sharpe = (excess.mean() / r.std()) * np.sqrt(252) if r.std() > 0 else np.nan
        rows.append({"amfi_code": code, "sharpe_ratio": sharpe})
    return pd.DataFrame(rows)


def compute_sortino(daily_returns: pd.DataFrame) -> pd.DataFrame:
    """Annualised Sortino ratio per fund: uses downside (negative-day-only) std as the denominator."""
    rf_daily = RISK_FREE_RATE / 252
    rows = []
    for code in daily_returns.columns:
        r = daily_returns[code].dropna()
        excess = r - rf_daily
        downside = r[r < 0]
        downside_std = downside.std() if len(downside) > 1 else np.nan
        sortino = (excess.mean() / downside_std) * np.sqrt(252) if downside_std and downside_std > 0 else np.nan
        rows.append({"amfi_code": code, "sortino_ratio": sortino})
    return pd.DataFrame(rows)


def compute_alpha_beta(daily_returns: pd.DataFrame) -> pd.DataFrame:
    """Alpha/Beta vs Nifty 100 via OLS regression (scipy.stats.linregress)."""
    benchmarks = pd.read_csv(RAW_DIR / "10_benchmark_indices.csv", parse_dates=["date"])
    nifty100 = benchmarks[benchmarks["index_name"] == "NIFTY100"].sort_values("date").set_index("date")["close_value"]
    nifty100_returns = nifty100.pct_change().dropna()

    rows = []
    for code in daily_returns.columns:
        fund_r = daily_returns[code].dropna()
        aligned = pd.concat([fund_r, nifty100_returns], axis=1, join="inner").dropna()
        aligned.columns = ["fund", "benchmark"]
        if len(aligned) < 30:
            continue
        slope, intercept, r_value, _, _ = stats.linregress(aligned["benchmark"], aligned["fund"])
        rows.append({"amfi_code": code, "alpha": intercept * 252, "beta": slope, "r_squared": r_value ** 2})
    return pd.DataFrame(rows)


def compute_max_drawdown(nav_wide: pd.DataFrame) -> pd.DataFrame:
    """Max drawdown and its peak/trough date range per fund."""
    rows = []
    for code in nav_wide.columns:
        series = nav_wide[code].dropna()
        running_max = series.cummax()
        drawdown = series / running_max - 1
        trough_date = drawdown.idxmin()
        peak_date = series.loc[:trough_date].idxmax()
        rows.append({
            "amfi_code": code,
            "max_drawdown_pct": drawdown.min() * 100,
            "peak_date": peak_date.date(),
            "trough_date": trough_date.date(),
        })
    return pd.DataFrame(rows)


def build_scorecard(fund_master, cagr_df, sharpe_df, alpha_beta_df, max_dd_df) -> pd.DataFrame:
    """Composite 0-100 fund score: 30% 3yr return + 25% Sharpe + 20% Alpha + 15% inverse expense ratio + 10% inverse max DD."""
    scorecard = fund_master[["amfi_code", "scheme_name", "fund_house", "category", "expense_ratio_pct"]].copy()
    scorecard = scorecard.merge(cagr_df[["amfi_code", "cagr_3yr"]], on="amfi_code", how="left")
    scorecard = scorecard.merge(sharpe_df[["amfi_code", "sharpe_ratio"]], on="amfi_code", how="left")
    scorecard = scorecard.merge(alpha_beta_df[["amfi_code", "alpha"]], on="amfi_code", how="left")
    scorecard = scorecard.merge(max_dd_df[["amfi_code", "max_drawdown_pct"]], on="amfi_code", how="left")

    scorecard["rank_3yr_return"] = scorecard["cagr_3yr"].rank(pct=True) * 100
    scorecard["rank_sharpe"] = scorecard["sharpe_ratio"].rank(pct=True) * 100
    scorecard["rank_alpha"] = scorecard["alpha"].rank(pct=True) * 100
    scorecard["rank_expense_inv"] = (1 - scorecard["expense_ratio_pct"].rank(pct=True)) * 100
    scorecard["rank_maxdd_inv"] = scorecard["max_drawdown_pct"].rank(pct=True) * 100

    scorecard["fund_score"] = (
        0.30 * scorecard["rank_3yr_return"]
        + 0.25 * scorecard["rank_sharpe"]
        + 0.20 * scorecard["rank_alpha"]
        + 0.15 * scorecard["rank_expense_inv"]
        + 0.10 * scorecard["rank_maxdd_inv"]
    ).round(2)

    scorecard = scorecard.sort_values("fund_score", ascending=False).reset_index(drop=True)
    scorecard["overall_rank"] = scorecard.index + 1
    return scorecard[["overall_rank", "amfi_code", "scheme_name", "fund_house", "category",
                       "fund_score", "cagr_3yr", "sharpe_ratio", "alpha",
                       "expense_ratio_pct", "max_drawdown_pct"]]


def run():
    """Compute all metrics end to end and write CSVs to data/outputs/."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fund_master = pd.read_csv(RAW_DIR / "01_fund_master.csv")

    print("Loading NAV data...")
    nav_wide, daily_returns = load_nav_wide()

    print("Computing CAGR (1/3/5yr, trading-day annualised)...")
    cagr_df = compute_cagr(nav_wide).merge(
        fund_master[["amfi_code", "scheme_name", "fund_house", "category"]], on="amfi_code", how="left"
    ).sort_values("cagr_3yr", ascending=False)
    cagr_df.to_csv(OUTPUT_DIR / "cagr_report.csv", index=False)

    print("Computing Sharpe ratio...")
    sharpe_df = compute_sharpe(daily_returns).merge(
        fund_master[["amfi_code", "scheme_name", "fund_house"]], on="amfi_code", how="left"
    ).sort_values("sharpe_ratio", ascending=False).reset_index(drop=True)
    sharpe_df["rank"] = sharpe_df.index + 1
    sharpe_df.to_csv(OUTPUT_DIR / "sharpe_values.csv", index=False)

    print("Computing Sortino ratio...")
    sortino_df = compute_sortino(daily_returns).merge(
        fund_master[["amfi_code", "scheme_name", "fund_house"]], on="amfi_code", how="left"
    ).sort_values("sortino_ratio", ascending=False).reset_index(drop=True)
    sortino_df["rank"] = sortino_df.index + 1
    sortino_df.to_csv(OUTPUT_DIR / "sortino_values.csv", index=False)

    print("Computing Alpha/Beta vs Nifty 100...")
    alpha_beta_df = compute_alpha_beta(daily_returns).merge(
        fund_master[["amfi_code", "scheme_name", "fund_house", "category"]], on="amfi_code", how="left"
    ).sort_values("alpha", ascending=False)
    alpha_beta_df.to_csv(OUTPUT_DIR / "alpha_beta.csv", index=False)

    print("Computing Max Drawdown...")
    max_dd_df = compute_max_drawdown(nav_wide).merge(
        fund_master[["amfi_code", "scheme_name", "fund_house"]], on="amfi_code", how="left"
    ).sort_values("max_drawdown_pct")
    max_dd_df.to_csv(OUTPUT_DIR / "max_drawdown.csv", index=False)

    print("Building fund scorecard...")
    scorecard = build_scorecard(fund_master, cagr_df, sharpe_df, alpha_beta_df, max_dd_df)
    scorecard.to_csv(OUTPUT_DIR / "fund_scorecard.csv", index=False)

    print(f"\nAll metrics written to {OUTPUT_DIR}")
    print(f"Top fund by scorecard: {scorecard.iloc[0]['scheme_name']} (score={scorecard.iloc[0]['fund_score']})")


if __name__ == "__main__":
    run()

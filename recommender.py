"""
Day 6 — Simple Fund Recommendation Logic
Bluestock Fintech | Mutual Fund Analytics Capstone

Given an investor's risk appetite (Low / Moderate / High), returns the top 3
funds by Sharpe ratio within the matching risk grade.

Usage as a script:
    python3 recommender.py Moderate

Usage as a module:
    from recommender import recommend_funds
    recommend_funds("High", top_n=3)
"""
import sys
import pandas as pd

RAW = "data/raw/"

# Maps a plain-language investor risk appetite to the fund risk_category
# values present in the fund master data.
RISK_MAP = {
    "Low": ["Low"],
    "Moderate": ["Moderate", "Moderately High"],
    "High": ["High", "Very High"],
}


def load_fund_performance():
    """Joins fund master with Day 4's Sharpe ratio ranking."""
    fund_master = pd.read_csv(RAW + "01_fund_master.csv")
    sharpe_df = pd.read_csv("sharpe_values.csv")
    fund_perf = fund_master[
        ["amfi_code", "scheme_name", "fund_house", "category", "risk_category"]
    ].merge(sharpe_df[["amfi_code", "sharpe_ratio"]], on="amfi_code", how="left")
    return fund_perf


def recommend_funds(risk_appetite, top_n=3, fund_perf=None):
    """
    Return the top N funds by Sharpe ratio matching the investor's risk appetite.

    Parameters
    ----------
    risk_appetite : str
        One of "Low", "Moderate", "High".
    top_n : int
        Number of funds to return (default 3).
    fund_perf : pd.DataFrame, optional
        Pre-loaded fund performance table. Loaded fresh if not provided.

    Returns
    -------
    pd.DataFrame with columns: scheme_name, fund_house, category,
    risk_category, sharpe_ratio
    """
    if risk_appetite not in RISK_MAP:
        raise ValueError(
            f"risk_appetite must be one of {list(RISK_MAP.keys())}, got '{risk_appetite}'"
        )
    if fund_perf is None:
        fund_perf = load_fund_performance()

    matching_grades = RISK_MAP[risk_appetite]
    candidates = fund_perf[fund_perf["risk_category"].isin(matching_grades)]
    top_funds = candidates.sort_values("sharpe_ratio", ascending=False).head(top_n)
    return top_funds[["scheme_name", "fund_house", "category", "risk_category", "sharpe_ratio"]]


def main():
    fund_perf = load_fund_performance()

    if len(sys.argv) > 1:
        risk_levels = [sys.argv[1]]
    else:
        risk_levels = ["Low", "Moderate", "High"]

    for risk in risk_levels:
        print(f"\n=== Recommendations for '{risk}' risk appetite ===")
        try:
            print(recommend_funds(risk, fund_perf=fund_perf).to_string(index=False))
        except ValueError as e:
            print(e)


if __name__ == "__main__":
    main()

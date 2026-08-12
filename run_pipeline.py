"""
run_pipeline.py

Bluestock Fintech | Mutual Fund Analytics Capstone
Master execution script. Runs the full pipeline end to end:

    1. ETL (ingest raw CSVs -> clean -> load to SQLite)
    2. Performance metrics (CAGR, Sharpe, Sortino, Alpha/Beta, Max Drawdown, Scorecard)
    3. Fund recommender smoke test (confirms it runs against fresh output)

This does NOT regenerate the notebooks (EDA, dashboard prep) or the Power BI
dashboard itself — those are run manually per README.md, since they involve
interactive tools (Jupyter, Power BI Desktop) rather than a one-shot script.

Usage:
    python3 run_pipeline.py
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))

import etl_pipeline
import compute_metrics
import recommender


def run():
    start = time.time()

    print("=" * 60)
    print("BLUESTOCK MF CAPSTONE — FULL PIPELINE RUN")
    print("=" * 60)

    print("\n[1/3] Running ETL pipeline...")
    etl_pipeline.run()

    print("\n[2/3] Computing performance metrics...")
    compute_metrics.run()

    print("\n[3/3] Fund recommender smoke test...")
    fund_perf = recommender.load_fund_performance()
    for risk in ["Low", "Moderate", "High"]:
        result = recommender.recommend_funds(risk, fund_perf=fund_perf)
        print(f"  {risk:10s} risk -> top pick: {result.iloc[0]['scheme_name']}")

    elapsed = time.time() - start
    print("\n" + "=" * 60)
    print(f"Pipeline complete in {elapsed:.1f}s")
    print("Next: run the notebooks in notebooks/ for EDA and advanced analytics,")
    print("and open dashboard/bluestock_mf_dashboard.pbix in Power BI Desktop.")
    print("=" * 60)


if __name__ == "__main__":
    run()

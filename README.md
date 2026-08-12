# Bluestock MF Analytics Capstone

End-to-end mutual fund analytics project: ETL pipeline → SQLite data warehouse → exploratory data analysis → fund performance analytics → Power BI dashboard → advanced risk/recommendation analytics.

Covers 40 mutual fund schemes across 10 fund houses, ~5,000 investors, and ~33,000 transactions, spanning January 2022 – May 2026.

## Project overview

| Phase | What it covers | Key outputs |
|---|---|---|
| ETL | Ingest 10 raw CSVs, validate, clean, load to SQLite | `data/db/bluestock_mf.db`, `data/processed/*.csv` |
| EDA | 18 charts covering NAV trends, AUM growth, SIP inflows, investor demographics, geography, correlations, sector allocation | `notebooks/03_eda_analysis.ipynb`, `charts/` |
| Performance Analytics | CAGR, Sharpe, Sortino, Alpha/Beta, Max Drawdown, composite fund scorecard | `notebooks/04_performance_analytics.ipynb`, `data/outputs/*.csv` |
| Dashboard | 4-page interactive Power BI dashboard: Industry Overview, Fund Performance, Investor Analytics, SIP & Market Trends | `dashboard/bluestock_mf_dashboard.pbix` |
| Advanced Analytics | VaR/CVaR, rolling Sharpe, investor cohort analysis, SIP continuity/at-risk flagging, sector concentration (HHI), fund recommender | `notebooks/05_advanced_analytics.ipynb`, `scripts/recommender.py` |

## Folder structure

```
bluestock_mf_capstone/
├── data/
│   ├── raw/            10 original source CSVs (untouched)
│   ├── processed/      cleaned CSVs written by the ETL pipeline
│   ├── outputs/         computed metrics CSVs (CAGR, Sharpe, scorecard, VaR, etc.)
│   └── db/              bluestock_mf.db (SQLite — regenerated locally, not committed)
├── notebooks/
│   ├── 01_data_ingestion.ipynb
│   ├── 02_data_cleaning.ipynb
│   ├── 03_eda_analysis.ipynb
│   ├── 04_performance_analytics.ipynb
│   └── 05_advanced_analytics.ipynb
├── scripts/
│   ├── etl_pipeline.py       ingest -> clean -> load to SQLite
│   ├── compute_metrics.py    CAGR / Sharpe / Sortino / Alpha-Beta / MaxDD / scorecard
│   ├── recommender.py        risk-appetite-based fund recommendation logic
│   └── live_nav_fetch.py     optional live NAV fetch from mfapi.in
├── sql/
│   ├── schema.sql
│   └── queries.sql
├── charts/               PNG exports from the notebooks
├── dashboard/
│   ├── bluestock_mf_dashboard.pbix
│   ├── Dashboard.pdf
│   └── dashboard_page*.png
├── reports/
│   ├── Final_Report.pdf
│   └── Bluestock_MF_Presentation.pptx
├── run_pipeline.py       master script: runs ETL + metrics end to end
├── requirements.txt
├── .gitignore
└── README.md
```

## Setup

```bash
git clone <this-repo-url>
cd bluestock_mf_capstone

python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

## Running the ETL pipeline

The fastest way to get a fully working local copy of everything (database + all computed metrics) is the master script:

```bash
python3 run_pipeline.py
```

This runs, in order:
1. **ETL** (`scripts/etl_pipeline.py`) — ingests the 10 raw CSVs from `data/raw/`, validates them, cleans NAV/transactions/performance data, and loads `dim_fund`, `dim_date`, `fact_nav`, `fact_transactions`, `fact_performance` into `data/db/bluestock_mf.db`
2. **Metrics** (`scripts/compute_metrics.py`) — computes CAGR, Sharpe, Sortino, Alpha/Beta, Max Drawdown, and the composite fund scorecard, writing results to `data/outputs/`
3. **Recommender smoke test** — confirms `scripts/recommender.py` runs correctly against the freshly computed metrics

Takes a few seconds. No manual steps required.

To run stages individually:
```bash
python3 scripts/etl_pipeline.py
python3 scripts/compute_metrics.py
python3 scripts/recommender.py Moderate   # or Low / High
```

**Note on the SQLite database:** `bluestock_mf.db` is **not committed to this repo** (see `.gitignore`) — it's a regenerable build artifact, not source data. Run `run_pipeline.py` to build it locally. The schema is documented in `sql/schema.sql` if you want to inspect the structure without running anything.

## Running the notebooks

Each notebook is self-contained and can be run independently (`Kernel → Restart & Run All` in Jupyter), as long as `data/raw/` and `data/processed/` are populated (run the ETL pipeline first if `data/processed/` is empty):

```bash
jupyter notebook notebooks/
```

- `03_eda_analysis.ipynb` — generates 18 charts into `charts/`
- `04_performance_analytics.ipynb` — generates the CSVs in `data/outputs/`
- `05_advanced_analytics.ipynb` — generates VaR/CVaR, rolling Sharpe, cohort, SIP continuity, and sector HHI outputs

## Opening the dashboard

1. Open `dashboard/bluestock_mf_dashboard.pbix` in **Power BI Desktop** (Windows only; see note below for Linux/Mac)
2. If prompted to refresh data sources, point Power BI at `data/outputs/` and `data/raw/` on your machine — the `.pbix` stores its own data model but source paths may need re-pointing after cloning
3. Static exports are also available without Power BI installed: `dashboard/Dashboard.pdf` and the individual `dashboard_page*.png` files

**Linux/Mac users:** Power BI Desktop is Windows-only. A Postgres + Metabase Docker alternative is documented for building an equivalent interactive dashboard without Windows — see `docker-compose.yml` and `load_to_postgres.py` if included in this repo, or the dashboard section of `reports/Final_Report.pdf` for details.

## Dataset descriptions

| File | Description |
|---|---|
| `01_fund_master.csv` | 40 schemes: name, fund house, category, sub-category, risk grade |
| `02_nav_history.csv` | Daily NAV per scheme, Jan 2022 – May 2026 |
| `03_aum_by_fund_house.csv` | AUM snapshots by fund house at 9 points in time |
| `04_monthly_sip_inflows.csv` | Industry-wide monthly SIP inflow, Jan 2022 – Dec 2025 |
| `05_category_inflows.csv` | Net inflow by fund category, by month |
| `06_industry_folio_count.csv` | Total industry folio count, by month |
| `07_scheme_performance.csv` | Pre-computed return/risk metrics per scheme (used for cross-checking) |
| `08_investor_transactions.csv` | ~33,000 investor-level SIP/Lumpsum/Redemption transactions |
| `09_portfolio_holdings.csv` | Sector-level portfolio weights for equity schemes |
| `10_benchmark_indices.csv` | Daily close values for 7 benchmark indices (Nifty 50, Nifty 100, etc.) |

Full column-level definitions are in `data_disctonary.md`.

## Known limitations

- **Alpha/Beta vs Nifty 100** shows very low R² (median < 0.01) across all 40 funds — the synthetic NAV series in this dataset move largely independently of the benchmark index. The regression methodology is correct; this is a property of the underlying synthetic data, not a calculation error. See `reports/Final_Report.pdf` for detail.
- **SIP continuity ("at-risk") flagging** shows ~98% of eligible investors flagged, because SIP transaction dates in this dataset are scattered over a wide window rather than a strict monthly cadence. The logic is correct and will behave as expected on real SIP data with realistic monthly timing.

## License / attribution

Built as a capstone project. Synthetic dataset — not real fund or investor data.

"""
scripts/live_nav_fetch.py

Bluestock Fintech | Mutual Fund Analytics Capstone
Fetches the latest published NAV for a handful of key schemes from the
public mfapi.in API and writes it to data/raw/live_nav_data.csv.

This is a standalone supplementary script (not part of run_pipeline.py,
since it depends on external network access and isn't required for the
core analytics). See Bonus Challenge B1 in the project brief for turning
this into a scheduled cron job.

Usage:
    python3 scripts/live_nav_fetch.py
"""
from pathlib import Path

import pandas as pd
import requests

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = BASE_DIR / "data" / "raw" / "live_nav_data.csv"
REQUEST_TIMEOUT_SECONDS = 10

# A representative sample of key schemes, not the full 40-fund universe —
# extend this dict to cover more schemes as needed.
SCHEMES = {
    "HDFC Top 100 Direct": 125497,
    "SBI Bluechip": 119551,
    "ICICI Bluechip": 120503,
    "Nippon Large Cap": 118632,
    "Axis Bluechip": 119092,
    "Kotak Bluechip": 120841,
}


def fetch_nav(scheme_code: int) -> dict | None:
    """Fetch the most recent NAV entry for a single scheme code from mfapi.in."""
    url = f"https://api.mfapi.in/mf/{scheme_code}"
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"  Failed to fetch scheme {scheme_code}: {e}")
        return None

    data = response.json()
    if not data.get("data"):
        print(f"  No NAV data returned for scheme {scheme_code}")
        return None

    latest = data["data"][0]
    return {
        "amfi_code": scheme_code,
        "fund_name": data["meta"]["scheme_name"],
        "date": latest["date"],
        "nav": latest["nav"],
    }


def run() -> pd.DataFrame:
    """Fetch NAV for every scheme in SCHEMES and write the result to disk."""
    print("Fetching live NAV data...")
    results = []
    for name, code in SCHEMES.items():
        print(f"  {name} ({code})...")
        nav_data = fetch_nav(code)
        if nav_data:
            results.append(nav_data)

    if not results:
        print("No data fetched.")
        return pd.DataFrame()

    df = pd.DataFrame(results)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"\nSaved {len(df)} rows to {OUTPUT_PATH}")
    return df


if __name__ == "__main__":
    run()

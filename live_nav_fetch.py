import requests
import pandas as pd
import os

# Key schemes to fetch
SCHEMES = {
    "HDFC Top 100 Direct": 125497,
    "SBI Bluechip": 119551,
    "ICICI Bluechip": 120503,
    "Nippon Large Cap": 118632,
    "Axis Bluechip": 119092,
    "Kotak Bluechip": 120841
}

def fetch_nav(scheme_code):
    url = f"https://api.mfapi.in/mf/{scheme_code}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        # The API returns 'meta' and 'data'. We want the latest NAV from 'data'
        if 'data' in data and len(data['data']) > 0:
            latest_data = data['data'][0]
            return {
                "amfi_code": scheme_code,
                "fund_name": data['meta']['scheme_name'],
                "date": latest_data['date'],
                "nav": latest_data['nav']
            }
    else:
        print(f"Failed to fetch data for scheme: {scheme_code}")
    return None

def main():
    print("Fetching live NAV data...")
    results = []
    
    for name, code in SCHEMES.items():
        print(f"Fetching {name} ({code})...")
        nav_data = fetch_nav(code)
        if nav_data:
            results.append(nav_data)
            
    if results:
        df = pd.DataFrame(results)
        output_path = "data/raw/live_nav_data.csv"
        df.to_csv(output_path, index=False)
        print(f"\nSuccessfully saved live NAV data to {output_path}")
        print(df)
    else:
        print("No data fetched.")

if __name__ == "__main__":
    main()
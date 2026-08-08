import pandas as pd
from sqlalchemy import create_engine
import os

# Define paths
RAW_DIR = "data/raw/"
PROCESSED_DIR = "data/processed/"
DB_PATH = "sqlite:///bluestock_mf.db"

def clean_data():
    print("Cleaning nav_history...")
    df_nav = pd.read_csv(f"{RAW_DIR}02_nav_history.csv")
    # Parse dates, sort, forward-fill missing NAVs, drop duplicates, and validate > 0
    df_nav['date'] = pd.to_datetime(df_nav['date'])
    df_nav = df_nav.sort_values(by=['amfi_code', 'date'])
    df_nav['nav'] = df_nav.groupby('amfi_code')['nav'].ffill()
    df_nav = df_nav.drop_duplicates()
    df_nav = df_nav[df_nav['nav'] > 0]
    df_nav.to_csv(f"{PROCESSED_DIR}cleaned_nav_history.csv", index=False)

    print("Cleaning investor_transactions...")
    df_trans = pd.read_csv(f"{RAW_DIR}08_investor_transactions.csv")
    # Standardize transaction type, validate amount, fix dates
    df_trans['transaction_type'] = df_trans['transaction_type'].str.capitalize()
    df_trans = df_trans[df_trans['amount_inr'] > 0]
    df_trans['transaction_date'] = pd.to_datetime(df_trans['transaction_date'])
    # Check KYC status
    valid_kyc = ['Verified', 'Pending', 'Rejected']
    df_trans = df_trans[df_trans['kyc_status'].isin(valid_kyc)]
    df_trans.to_csv(f"{PROCESSED_DIR}cleaned_investor_transactions.csv", index=False)

    print("Cleaning scheme_performance...")
    df_perf = pd.read_csv(f"{RAW_DIR}07_scheme_performance.csv")
    print("Cleaning scheme_performance...")
    df_perf = pd.read_csv(f"{RAW_DIR}07_scheme_performance.csv")
    
    # Check expense ratio range (0.1% - 2.5%) using the correct column name
    df_perf['expense_ratio_pct'] = pd.to_numeric(df_perf['expense_ratio_pct'], errors='coerce')
    df_perf = df_perf[(df_perf['expense_ratio_pct'] >= 0.1) & (df_perf['expense_ratio_pct'] <= 2.5)]
    
    # Update the return columns to match your CSV headers
    return_cols = ['return_1yr_pct', 'return_3yr_pct', 'return_5yr_pct']
    for col in return_cols:
        df_perf[col] = pd.to_numeric(df_perf[col], errors='coerce')
        
    df_perf.to_csv(f"{PROCESSED_DIR}cleaned_scheme_performance.csv", index=False)
    return df_nav, df_trans, df_perf

def load_to_sqlite(df_nav, df_trans, df_perf):
    print("\nLoading datasets into SQLite database...")
    engine = create_engine(DB_PATH)
    
    # Load cleaned dataframes directly into SQL tables
    df_nav.to_sql('fact_nav', engine, if_exists='replace', index=False)
    df_trans.to_sql('fact_transactions', engine, if_exists='replace', index=False)
    df_perf.to_sql('fact_performance', engine, if_exists='replace', index=False)
    
    print("Database loaded successfully: bluestock_mf.db")

if __name__ == "__main__":
    df_nav, df_trans, df_perf = clean_data()
    load_to_sqlite(df_nav, df_trans, df_perf)
import pandas as pd
import os

# Define the path to raw data
DATA_DIR = "data/raw/"

# List of the 10 CSV files based on your screenshot
csv_files = [
    "01_fund_master.csv", "02_nav_history.csv", "03_aum_by_fund_house.csv",
    "04_monthly_sip_inflows.csv", "05_category_inflows.csv", "06_industry_folio_count.csv",
    "07_scheme_performance.csv", "08_investor_transactions.csv", "09_portfolio_holdings.csv",
    "10_benchmark_indices.csv"
]

def load_and_inspect():
    datasets = {}
    for file in csv_files:
        filepath = os.path.join(DATA_DIR, file)
        if os.path.exists(filepath):
            print(f"\n--- Inspecting {file} ---")
            df = pd.read_csv(filepath)
            datasets[file] = df
            
            # Print shape, dtypes, and head
            print(f"Shape: {df.shape}")
            print(f"Data Types:\n{df.dtypes}\n")
            print(f"Head:\n{df.head(3)}\n")
        else:
            print(f"File not found: {filepath}. Please ensure it is in the data/raw/ directory.")
    
    return datasets

def explore_fund_master(fund_master_df):
    print("\n--- Exploring Fund Master ---")
    if 'fund_house' in fund_master_df.columns:
        print(f"Unique Fund Houses: {fund_master_df['fund_house'].nunique()}")
    if 'category' in fund_master_df.columns:
        print(f"Categories: {fund_master_df['category'].unique()}")
    if 'sub_category' in fund_master_df.columns:
        print(f"Sub-categories: {fund_master_df['sub_category'].nunique()}")
    if 'risk_grade' in fund_master_df.columns:
        print(f"Risk Grades: {fund_master_df['risk_grade'].unique()}")

def validate_amfi_codes(fund_master_df, nav_history_df):
    print("\n--- Validating AMFI Codes ---")
    # Assuming the column names are 'amfi_code', adjust if they differ in your CSV
    if 'amfi_code' in fund_master_df.columns and 'amfi_code' in nav_history_df.columns:
        master_codes = set(fund_master_df['amfi_code'].unique())
        nav_codes = set(nav_history_df['amfi_code'].unique())
        
        missing_in_nav = master_codes - nav_codes
        if not missing_in_nav:
            print("Validation Successful: Every AMFI code in fund_master exists in nav_history.")
        else:
            print(f"Validation Warning: {len(missing_in_nav)} codes from fund_master are missing in nav_history.")
    else:
        print("Column 'amfi_code' not found. Please check your CSV column headers.")

if __name__ == "__main__":
    data_dict = load_and_inspect()
    
    # Run exploration and validation if the required files loaded successfully
    if "01_fund_master.csv" in data_dict and "02_nav_history.csv" in data_dict:
        explore_fund_master(data_dict["01_fund_master.csv"])
        validate_amfi_codes(data_dict["01_fund_master.csv"], data_dict["02_nav_history.csv"])
-- Star Schema Design for Mutual Fund Database

-- Dimension: Fund Master
CREATE TABLE dim_fund (
    amfi_code INTEGER PRIMARY KEY,
    scheme_name TEXT,
    fund_house TEXT,
    category TEXT,
    sub_category TEXT,
    risk_grade TEXT
);

-- Dimension: Date
CREATE TABLE dim_date (
    date_id TEXT PRIMARY KEY, -- Format: YYYY-MM-DD
    year INTEGER,
    month INTEGER,
    day INTEGER,
    quarter INTEGER,
    is_weekend BOOLEAN
);

-- Fact: NAV History
CREATE TABLE fact_nav (
    nav_id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code INTEGER,
    date TEXT,
    nav REAL,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date) REFERENCES dim_date(date_id)
);

-- Fact: Investor Transactions
CREATE TABLE fact_transactions (
    transaction_id TEXT PRIMARY KEY,
    transaction_date TEXT,
    amfi_code INTEGER,
    transaction_type TEXT,
    amount_inr REAL,
    state TEXT,
    city TEXT,
    city_tier TEXT,
    age_group TEXT,
    gender TEXT,
    payment_mode TEXT,
    kyc_status TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (transaction_date) REFERENCES dim_date(date_id)
);

-- Fact: Scheme Performance
CREATE TABLE fact_performance (
    amfi_code INTEGER PRIMARY KEY,
    scheme_name TEXT,
    return_1yr_pct REAL,
    return_3yr_pct REAL,
    return_5yr_pct REAL,
    aum_crore REAL,
    expense_ratio_pct REAL,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);
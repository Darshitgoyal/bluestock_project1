# Mutual Fund Data Dictionary

## 1. dim_fund (Fund Master)
*   **amfi_code (INT):** Unique Association of Mutual Funds in India identifier (Primary Key).
*   **scheme_name (TEXT):** Full official name of the mutual fund scheme.
*   **fund_house (TEXT):** The AMC (Asset Management Company) managing the fund.
*   **category (TEXT):** High-level classification (e.g., Equity, Debt).
*   **risk_grade (TEXT):** Risk assessment level (e.g., Low, High, Very High).

## 2. fact_nav (NAV History)
*   **amfi_code (INT):** Foreign key linking to dim_fund.
*   **date (TEXT):** Date of the NAV recording (YYYY-MM-DD).
*   **nav (REAL):** Net Asset Value of the fund on that specific date.

## 3. fact_transactions (Investor Transactions)
*   **transaction_date (TEXT):** Date the transaction was executed.
*   **transaction_type (TEXT):** Type of transaction (SIP, Lumpsum, Redemption).
*   **amount_inr (REAL):** Total transaction value in Indian Rupees.
*   **city_tier (TEXT):** Classification of the investor's city (e.g., T30, B30).
*   **kyc_status (TEXT):** Investor's verification status (Verified, Pending, Rejected).

## 4. fact_performance (Scheme Performance)
*   **return_1yr_pct (REAL):** 1-year trailing percentage return.
*   **return_3yr_pct (REAL):** 3-year trailing percentage return.
*   **aum_crore (REAL):** Assets Under Management in Crores.
*   **expense_ratio_pct (REAL):** The annual maintenance charge levied by mutual funds (must be between 0.1% - 2.5%).
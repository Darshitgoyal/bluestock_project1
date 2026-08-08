-- 1. Top 5 funds by AUM
SELECT scheme_name, aum_crore 
FROM fact_performance 
ORDER BY aum_crore DESC 
LIMIT 5;

-- 2. Average NAV per month (Using SQLite string functions for YYYY-MM)
SELECT substr(date, 1, 7) AS month, AVG(nav) AS avg_nav
FROM fact_nav
GROUP BY substr(date, 1, 7)
ORDER BY month;

-- 3. SIP YoY Growth (Total SIP amount per year)
SELECT substr(transaction_date, 1, 4) AS year, SUM(amount_inr) AS total_sip_volume
FROM fact_transactions
WHERE transaction_type = 'SIP'
GROUP BY substr(transaction_date, 1, 4)
ORDER BY year;

-- 4. Transactions by state
SELECT state, COUNT(*) as transaction_count, SUM(amount_inr) as total_volume
FROM fact_transactions
GROUP BY state
ORDER BY total_volume DESC;

-- 5. Funds with expense_ratio < 1%
SELECT scheme_name, expense_ratio_pct
FROM fact_performance
WHERE expense_ratio_pct < 1.0
ORDER BY expense_ratio_pct ASC;

-- 6. Most popular payment mode for Lumpsum investments
SELECT payment_mode, COUNT(*) as usage_count
FROM fact_transactions
WHERE transaction_type = 'Lumpsum'
GROUP BY payment_mode
ORDER BY usage_count DESC;

-- 7. Gender split of total investment amounts
SELECT gender, SUM(amount_inr) as total_invested
FROM fact_transactions
GROUP BY gender;

-- 8. Top 5 highest performing funds over 3 years
SELECT scheme_name, return_3yr_pct
FROM fact_performance
ORDER BY return_3yr_pct DESC
LIMIT 5;

-- 9. Transaction volume by City Tier
SELECT city_tier, COUNT(*) as total_transactions, SUM(amount_inr) as total_amount
FROM fact_transactions
GROUP BY city_tier
ORDER BY total_amount DESC;

-- 10. Failed or Pending KYC transactions
SELECT kyc_status, COUNT(*) as count, SUM(amount_inr) as exposed_amount
FROM fact_transactions
WHERE kyc_status != 'Verified'
GROUP BY kyc_status;
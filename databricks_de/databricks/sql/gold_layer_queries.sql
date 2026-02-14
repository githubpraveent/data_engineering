-- Sample SQL queries for Gold layer analytics
-- Use these queries with Databricks SQL Warehouses

-- ============================================================================
-- SALES ANALYTICS
-- ============================================================================

-- Total sales by day
SELECT
    d.date,
    d.day_name,
    SUM(fs.total_amount) AS total_sales,
    SUM(fs.profit_amount) AS total_profit,
    COUNT(DISTINCT fs.transaction_id) AS transaction_count
FROM retail_datalake.prod_gold.fact_sales fs
JOIN retail_datalake.prod_gold.dim_date d ON fs.date_key = d.date_key
WHERE d.date >= CURRENT_DATE() - INTERVAL 30 DAY
GROUP BY d.date, d.day_name
ORDER BY d.date DESC;

-- Sales by store
SELECT
    s.store_name,
    s.city,
    s.state,
    SUM(fs.total_amount) AS total_sales,
    SUM(fs.profit_amount) AS total_profit,
    SUM(fs.quantity) AS total_quantity,
    COUNT(DISTINCT fs.transaction_id) AS transaction_count
FROM retail_datalake.prod_gold.fact_sales fs
JOIN retail_datalake.prod_gold.dim_store s ON fs.store_key = s.store_key
WHERE fs.date_key >= YEAR(CURRENT_DATE()) * 10000 + MONTH(CURRENT_DATE()) * 100
GROUP BY s.store_name, s.city, s.state
ORDER BY total_sales DESC;

-- Sales by product category
SELECT
    p.category,
    p.subcategory,
    SUM(fs.total_amount) AS total_sales,
    SUM(fs.profit_amount) AS total_profit,
    SUM(fs.quantity) AS total_quantity,
    AVG(fs.unit_price) AS avg_unit_price
FROM retail_datalake.prod_gold.fact_sales fs
JOIN retail_datalake.prod_gold.dim_product p ON fs.product_key = p.product_key
WHERE p.is_current = TRUE
GROUP BY p.category, p.subcategory
ORDER BY total_sales DESC;

-- Top customers by sales
SELECT
    c.customer_id,
    c.full_name,
    c.city,
    c.state,
    SUM(fs.total_amount) AS total_sales,
    SUM(fs.profit_amount) AS total_profit,
    COUNT(DISTINCT fs.transaction_id) AS transaction_count,
    COUNT(DISTINCT fs.date_key) AS days_active
FROM retail_datalake.prod_gold.fact_sales fs
JOIN retail_datalake.prod_gold.dim_customer c ON fs.customer_key = c.customer_key
WHERE c.is_current = TRUE
GROUP BY c.customer_id, c.full_name, c.city, c.state
ORDER BY total_sales DESC
LIMIT 100;

-- Sales trend over time (monthly)
SELECT
    d.year,
    d.month,
    d.month_name,
    SUM(fs.total_amount) AS total_sales,
    SUM(fs.profit_amount) AS total_profit,
    COUNT(DISTINCT fs.transaction_id) AS transaction_count,
    AVG(fs.total_amount) AS avg_transaction_amount
FROM retail_datalake.prod_gold.fact_sales fs
JOIN retail_datalake.prod_gold.dim_date d ON fs.date_key = d.date_key
WHERE d.date >= CURRENT_DATE() - INTERVAL 12 MONTH
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year, d.month;

-- ============================================================================
-- CUSTOMER ANALYTICS
-- ============================================================================

-- Customer lifetime value
SELECT
    c.customer_id,
    c.full_name,
    c.registration_date,
    SUM(fs.total_amount) AS lifetime_value,
    SUM(fs.profit_amount) AS lifetime_profit,
    COUNT(DISTINCT fs.transaction_id) AS total_transactions,
    COUNT(DISTINCT fs.date_key) AS days_active,
    MIN(d.date) AS first_purchase_date,
    MAX(d.date) AS last_purchase_date
FROM retail_datalake.prod_gold.fact_sales fs
JOIN retail_datalake.prod_gold.dim_customer c ON fs.customer_key = c.customer_key
JOIN retail_datalake.prod_gold.dim_date d ON fs.date_key = d.date_key
WHERE c.is_current = TRUE
GROUP BY c.customer_id, c.full_name, c.registration_date
ORDER BY lifetime_value DESC;

-- Customer segmentation by purchase frequency
SELECT
    CASE
        WHEN days_active >= 30 THEN 'High Frequency'
        WHEN days_active >= 10 THEN 'Medium Frequency'
        ELSE 'Low Frequency'
    END AS customer_segment,
    COUNT(DISTINCT c.customer_id) AS customer_count,
    AVG(lifetime_value) AS avg_lifetime_value,
    AVG(total_transactions) AS avg_transactions
FROM (
    SELECT
        c.customer_id,
        SUM(fs.total_amount) AS lifetime_value,
        COUNT(DISTINCT fs.transaction_id) AS total_transactions,
        COUNT(DISTINCT fs.date_key) AS days_active
    FROM retail_datalake.prod_gold.fact_sales fs
    JOIN retail_datalake.prod_gold.dim_customer c ON fs.customer_key = c.customer_key
    WHERE c.is_current = TRUE
    GROUP BY c.customer_id
) AS customer_metrics
GROUP BY customer_segment;

-- ============================================================================
-- PRODUCT ANALYTICS
-- ============================================================================

-- Top selling products
SELECT
    p.product_id,
    p.product_name,
    p.category,
    p.brand,
    SUM(fs.quantity) AS total_quantity_sold,
    SUM(fs.total_amount) AS total_sales,
    SUM(fs.profit_amount) AS total_profit,
    AVG(fs.unit_price) AS avg_unit_price,
    COUNT(DISTINCT fs.date_key) AS days_sold
FROM retail_datalake.prod_gold.fact_sales fs
JOIN retail_datalake.prod_gold.dim_product p ON fs.product_key = p.product_key
WHERE p.is_current = TRUE
GROUP BY p.product_id, p.product_name, p.category, p.brand
ORDER BY total_quantity_sold DESC
LIMIT 50;

-- Product profitability analysis
SELECT
    p.category,
    p.brand,
    SUM(fs.total_amount) AS total_revenue,
    SUM(fs.cost_amount) AS total_cost,
    SUM(fs.profit_amount) AS total_profit,
    (SUM(fs.profit_amount) / SUM(fs.total_amount)) * 100 AS profit_margin_pct
FROM retail_datalake.prod_gold.fact_sales fs
JOIN retail_datalake.prod_gold.dim_product p ON fs.product_key = p.product_key
WHERE p.is_current = TRUE
GROUP BY p.category, p.brand
HAVING SUM(fs.total_amount) > 10000
ORDER BY profit_margin_pct DESC;

-- ============================================================================
-- TIME-BASED ANALYTICS
-- ============================================================================

-- Sales by day of week
SELECT
    d.day_of_week,
    d.day_name,
    AVG(daily_sales.total_sales) AS avg_daily_sales,
    AVG(daily_sales.transaction_count) AS avg_transaction_count
FROM (
    SELECT
        fs.date_key,
        SUM(fs.total_amount) AS total_sales,
        COUNT(DISTINCT fs.transaction_id) AS transaction_count
    FROM retail_datalake.prod_gold.fact_sales fs
    WHERE fs.date_key >= YEAR(CURRENT_DATE()) * 10000
    GROUP BY fs.date_key
) AS daily_sales
JOIN retail_datalake.prod_gold.dim_date d ON daily_sales.date_key = d.date_key
GROUP BY d.day_of_week, d.day_name
ORDER BY d.day_of_week;

-- Sales by hour of day (if timestamp available)
SELECT
    HOUR(fs.transaction_timestamp) AS hour_of_day,
    SUM(fs.total_amount) AS total_sales,
    COUNT(DISTINCT fs.transaction_id) AS transaction_count,
    AVG(fs.total_amount) AS avg_transaction_amount
FROM retail_datalake.prod_gold.fact_sales fs
WHERE fs.date_key >= YEAR(CURRENT_DATE()) * 10000 + MONTH(CURRENT_DATE()) * 100
GROUP BY HOUR(fs.transaction_timestamp)
ORDER BY hour_of_day;

-- ============================================================================
-- AGGREGATE QUERIES (Using Pre-aggregated Tables)
-- ============================================================================

-- Daily sales summary (using aggregate table if available)
SELECT
    d.date,
    d.day_name,
    agg.total_quantity,
    agg.total_sales_amount,
    agg.total_profit_amount,
    agg.transaction_count
FROM retail_datalake.prod_gold.agg_daily_sales agg
JOIN retail_datalake.prod_gold.dim_date d ON agg.date_key = d.date_key
WHERE d.date >= CURRENT_DATE() - INTERVAL 30 DAY
ORDER BY d.date DESC;


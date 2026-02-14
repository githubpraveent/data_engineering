-- Update Analytics/Aggregated Tables
-- These queries populate or update aggregated tables for reporting

-- Daily Sales Summary
CREATE OR REPLACE TABLE `{project_id}.{analytics_dataset}.daily_sales_summary`
PARTITION BY transaction_date
CLUSTER BY transaction_date
AS
SELECT 
    DATE(sf.transaction_timestamp) AS transaction_date,
    COUNT(DISTINCT sf.transaction_id) AS total_transactions,
    COUNT(DISTINCT sf.customer_id) AS unique_customers,
    SUM(sf.total_amount) AS total_revenue,
    AVG(sf.total_amount) AS avg_transaction_value,
    COUNT(DISTINCT sf.product_id) AS unique_products,
    SUM(sf.quantity) AS total_quantity,
    CURRENT_TIMESTAMP() AS last_updated
FROM `{project_id}.{curated_dataset}.sales_fact` sf
WHERE DATE(sf.transaction_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
GROUP BY transaction_date
ORDER BY transaction_date DESC;

-- Monthly Sales Summary
CREATE OR REPLACE TABLE `{project_id}.{analytics_dataset}.monthly_sales_summary`
PARTITION BY DATE(year, month, 1)
CLUSTER BY year, month
AS
SELECT 
    EXTRACT(YEAR FROM sf.transaction_timestamp) AS year,
    EXTRACT(MONTH FROM sf.transaction_timestamp) AS month,
    COUNT(DISTINCT sf.transaction_id) AS total_transactions,
    COUNT(DISTINCT sf.customer_id) AS unique_customers,
    SUM(sf.total_amount) AS total_revenue,
    AVG(sf.total_amount) AS avg_transaction_value,
    COUNT(DISTINCT sf.product_id) AS unique_products,
    SUM(sf.quantity) AS total_quantity,
    CURRENT_TIMESTAMP() AS last_updated
FROM `{project_id}.{curated_dataset}.sales_fact` sf
WHERE DATE(sf.transaction_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 24 MONTH)
GROUP BY year, month
ORDER BY year DESC, month DESC;

-- Customer Lifetime Value
CREATE OR REPLACE TABLE `{project_id}.{analytics_dataset}.customer_lifetime_value`
CLUSTER BY customer_id, customer_segment
AS
SELECT 
    sf.customer_id,
    cd.customer_segment,
    MIN(DATE(sf.transaction_timestamp)) AS first_transaction_date,
    MAX(DATE(sf.transaction_timestamp)) AS last_transaction_date,
    COUNT(DISTINCT sf.transaction_id) AS total_transactions,
    SUM(sf.total_amount) AS total_revenue,
    AVG(sf.total_amount) AS avg_transaction_value,
    DATE_DIFF(MAX(DATE(sf.transaction_timestamp)), MIN(DATE(sf.transaction_timestamp)), DAY) AS days_active,
    CURRENT_TIMESTAMP() AS last_updated
FROM `{project_id}.{curated_dataset}.sales_fact` sf
INNER JOIN `{project_id}.{curated_dataset}.customer_dimension` cd
ON sf.customer_id = cd.customer_id
AND cd.is_current = TRUE
GROUP BY sf.customer_id, cd.customer_segment;

-- Product Performance Summary
CREATE OR REPLACE TABLE `{project_id}.{analytics_dataset}.product_performance`
CLUSTER BY product_id, category
AS
SELECT 
    sf.product_id,
    pd.product_name,
    pd.category,
    SUM(sf.quantity) AS total_quantity_sold,
    SUM(sf.total_amount) AS total_revenue,
    AVG(sf.unit_price) AS avg_selling_price,
    COUNT(DISTINCT sf.customer_id) AS unique_customers,
    COUNT(DISTINCT sf.store_id) AS unique_stores,
    MAX(DATE(sf.transaction_timestamp)) AS last_sale_date,
    CURRENT_TIMESTAMP() AS last_updated
FROM `{project_id}.{curated_dataset}.sales_fact` sf
INNER JOIN `{project_id}.{curated_dataset}.product_dimension` pd
ON sf.product_id = pd.product_id
AND pd.is_current = TRUE
GROUP BY sf.product_id, pd.product_name, pd.category;

-- Store Performance Summary
CREATE OR REPLACE TABLE `{project_id}.{analytics_dataset}.store_performance`
CLUSTER BY store_id, state
AS
SELECT 
    sf.store_id,
    sd.store_name,
    sd.state,
    COUNT(DISTINCT sf.transaction_id) AS total_transactions,
    SUM(sf.total_amount) AS total_revenue,
    AVG(sf.total_amount) AS avg_transaction_value,
    COUNT(DISTINCT sf.customer_id) AS unique_customers,
    COUNT(DISTINCT sf.product_id) AS unique_products,
    CURRENT_TIMESTAMP() AS last_updated
FROM `{project_id}.{curated_dataset}.sales_fact` sf
INNER JOIN `{project_id}.{curated_dataset}.store_dimension` sd
ON sf.store_id = sd.store_id
GROUP BY sf.store_id, sd.store_name, sd.state;


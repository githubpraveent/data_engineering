-- Create analytics/aggregated tables in BigQuery
-- These tables contain pre-aggregated data for reporting and dashboards

-- Daily Sales Summary
CREATE TABLE IF NOT EXISTS `{project_id}.{analytics_dataset}.daily_sales_summary`
(
    transaction_date DATE NOT NULL,
    total_transactions INTEGER,
    unique_customers INTEGER,
    total_revenue FLOAT64,
    avg_transaction_value FLOAT64,
    unique_products INTEGER,
    total_quantity INTEGER,
    last_updated TIMESTAMP
)
PARTITION BY transaction_date
CLUSTER BY transaction_date
OPTIONS(
    description="Daily aggregated sales metrics",
    labels=[("environment", "{environment}"), ("purpose", "analytics")]
);

-- Monthly Sales Summary
CREATE TABLE IF NOT EXISTS `{project_id}.{analytics_dataset}.monthly_sales_summary`
(
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    total_transactions INTEGER,
    unique_customers INTEGER,
    total_revenue FLOAT64,
    avg_transaction_value FLOAT64,
    unique_products INTEGER,
    total_quantity INTEGER,
    last_updated TIMESTAMP
)
PARTITION BY DATE(year, month, 1)
CLUSTER BY year, month
OPTIONS(
    description="Monthly aggregated sales metrics",
    labels=[("environment", "{environment}"), ("purpose", "analytics")]
);

-- Customer Lifetime Value
CREATE TABLE IF NOT EXISTS `{project_id}.{analytics_dataset}.customer_lifetime_value`
(
    customer_id STRING NOT NULL,
    first_transaction_date DATE,
    last_transaction_date DATE,
    total_transactions INTEGER,
    total_revenue FLOAT64,
    avg_transaction_value FLOAT64,
    days_active INTEGER,
    customer_segment STRING,
    last_updated TIMESTAMP
)
CLUSTER BY customer_id, customer_segment
OPTIONS(
    description="Customer lifetime value metrics",
    labels=[("environment", "{environment}"), ("purpose", "analytics")]
);

-- Product Performance Summary
CREATE TABLE IF NOT EXISTS `{project_id}.{analytics_dataset}.product_performance`
(
    product_id STRING NOT NULL,
    product_name STRING,
    category STRING,
    total_quantity_sold INTEGER,
    total_revenue FLOAT64,
    avg_selling_price FLOAT64,
    unique_customers INTEGER,
    unique_stores INTEGER,
    last_sale_date DATE,
    last_updated TIMESTAMP
)
CLUSTER BY product_id, category
OPTIONS(
    description="Product performance metrics",
    labels=[("environment", "{environment}"), ("purpose", "analytics")]
);

-- Store Performance Summary
CREATE TABLE IF NOT EXISTS `{project_id}.{analytics_dataset}.store_performance`
(
    store_id STRING NOT NULL,
    store_name STRING,
    state STRING,
    total_transactions INTEGER,
    total_revenue FLOAT64,
    avg_transaction_value FLOAT64,
    unique_customers INTEGER,
    unique_products INTEGER,
    last_updated TIMESTAMP
)
CLUSTER BY store_id, state
OPTIONS(
    description="Store performance metrics",
    labels=[("environment", "{environment}"), ("purpose", "analytics")]
);

-- Materialized View: Top Customers
CREATE MATERIALIZED VIEW IF NOT EXISTS `{project_id}.{analytics_dataset}.top_customers_mv`
PARTITION BY DATE_TRUNC(last_transaction_date, MONTH)
CLUSTER BY customer_segment
AS
SELECT 
    customer_id,
    customer_segment,
    total_revenue,
    total_transactions,
    last_transaction_date,
    CURRENT_TIMESTAMP() as last_updated
FROM `{project_id}.{analytics_dataset}.customer_lifetime_value`
WHERE total_revenue > 1000
ORDER BY total_revenue DESC
LIMIT 1000
OPTIONS(
    description="Materialized view of top customers by revenue",
    labels=[("environment", "{environment}"), ("purpose", "analytics")]
);


-- ============================================================================
-- Scenario D: Real-Time Aggregated Analytics with Dynamic Tables
-- Creates dynamic tables for minute-level and hour-level aggregations
-- ============================================================================

USE DATABASE DEV_DW;
USE SCHEMA MART;

-- ============================================================================
-- Dynamic Table: Minute-Level Sales Aggregation
-- Continuously updates minute-level metrics
-- ============================================================================

CREATE OR REPLACE DYNAMIC TABLE dt_sales_by_store_minute
  TARGET_LAG = '1 minute'  -- Update within 1 minute of source changes
  WAREHOUSE = WH_TRANS
  COMMENT = 'Real-time minute-level sales aggregation'
AS
SELECT
    DATE_TRUNC('minute', event_timestamp) AS minute_timestamp,
    store_id,
    product_id,
    
    -- Transaction metrics
    COUNT(DISTINCT CASE WHEN event_type = 'SALE' THEN transaction_id END) AS transaction_count,
    COUNT(CASE WHEN event_type = 'SALE' THEN 1 END) AS sale_events,
    COUNT(CASE WHEN event_type = 'REFUND' THEN 1 END) AS refund_events,
    
    -- Quantity metrics
    SUM(CASE WHEN event_type = 'SALE' THEN quantity ELSE 0 END) AS total_quantity_sold,
    SUM(CASE WHEN event_type = 'REFUND' THEN ABS(quantity) ELSE 0 END) AS total_quantity_refunded,
    
    -- Revenue metrics
    SUM(CASE WHEN event_type = 'SALE' THEN total_amount ELSE 0 END) AS total_sales_amount,
    SUM(CASE WHEN event_type = 'REFUND' THEN ABS(total_amount) ELSE 0 END) AS total_refund_amount,
    SUM(CASE WHEN event_type = 'SALE' THEN total_amount ELSE -total_amount END) AS net_sales_amount,
    
    -- Average metrics
    AVG(CASE WHEN event_type = 'SALE' THEN total_amount END) AS avg_transaction_amount,
    AVG(CASE WHEN event_type = 'SALE' THEN quantity END) AS avg_quantity_per_transaction,
    
    -- Time range
    MIN(event_timestamp) AS first_event_in_minute,
    MAX(event_timestamp) AS last_event_in_minute
    
FROM DEV_RAW.BRONZE.retail_events
WHERE event_type IN ('SALE', 'REFUND')
GROUP BY
    DATE_TRUNC('minute', event_timestamp),
    store_id,
    product_id;

-- ============================================================================
-- Dynamic Table: Hour-Level Sales Summary
-- Aggregates minute-level data into hourly summaries
-- ============================================================================

CREATE OR REPLACE DYNAMIC TABLE dt_sales_by_store_hour
  TARGET_LAG = '5 minutes'  -- Update within 5 minutes
  WAREHOUSE = WH_TRANS
  COMMENT = 'Real-time hour-level sales summary for BI consumption'
AS
SELECT
    DATE_TRUNC('hour', minute_timestamp) AS hour_timestamp,
    store_id,
    product_id,
    
    -- Aggregated metrics
    SUM(transaction_count) AS total_transactions,
    SUM(sale_events) AS total_sale_events,
    SUM(refund_events) AS total_refund_events,
    SUM(total_quantity_sold) AS total_quantity_sold,
    SUM(total_quantity_refunded) AS total_quantity_refunded,
    SUM(total_sales_amount) AS total_sales_amount,
    SUM(total_refund_amount) AS total_refund_amount,
    SUM(net_sales_amount) AS net_sales_amount,
    
    -- Calculated metrics
    AVG(avg_transaction_amount) AS avg_transaction_amount,
    AVG(avg_quantity_per_transaction) AS avg_quantity_per_transaction,
    
    -- Time range
    MIN(first_event_in_minute) AS hour_start,
    MAX(last_event_in_minute) AS hour_end
    
FROM dt_sales_by_store_minute
GROUP BY
    DATE_TRUNC('hour', minute_timestamp),
    store_id,
    product_id;

-- ============================================================================
-- Dynamic Table: Store-Level Daily Summary
-- Daily rollup for reporting
-- ============================================================================

CREATE OR REPLACE DYNAMIC TABLE dt_sales_by_store_day
  TARGET_LAG = '15 minutes'  -- Update within 15 minutes
  WAREHOUSE = WH_TRANS
  COMMENT = 'Daily sales summary by store'
AS
SELECT
    DATE(hour_timestamp) AS sales_date,
    store_id,
    
    -- Daily totals
    SUM(total_transactions) AS daily_transactions,
    SUM(total_sale_events) AS daily_sale_events,
    SUM(total_refund_events) AS daily_refund_events,
    SUM(total_quantity_sold) AS daily_quantity_sold,
    SUM(net_sales_amount) AS daily_net_sales,
    
    -- Peak hour metrics
    MAX(net_sales_amount) AS peak_hour_sales,
    ARRAY_AGG(hour_timestamp ORDER BY net_sales_amount DESC LIMIT 1)[0] AS peak_hour,
    
    -- Time range
    MIN(hour_start) AS day_start,
    MAX(hour_end) AS day_end
    
FROM dt_sales_by_store_hour
GROUP BY
    DATE(hour_timestamp),
    store_id;

-- ============================================================================
-- Dynamic Table: Real-Time Dashboard Metrics
-- Highly aggregated metrics for dashboards
-- ============================================================================

CREATE OR REPLACE DYNAMIC TABLE dt_realtime_dashboard
  TARGET_LAG = '30 seconds'  -- Near real-time (30 seconds)
  WAREHOUSE = WH_TRANS
  COMMENT = 'Real-time dashboard metrics with minimal latency'
AS
SELECT
    CURRENT_TIMESTAMP() AS snapshot_timestamp,
    
    -- Overall metrics
    COUNT(*) AS total_events_last_minute,
    COUNT(DISTINCT store_id) AS active_stores,
    COUNT(DISTINCT product_id) AS active_products,
    SUM(CASE WHEN event_type = 'SALE' THEN total_amount ELSE 0 END) AS total_sales_last_minute,
    SUM(CASE WHEN event_type = 'REFUND' THEN ABS(total_amount) ELSE 0 END) AS total_refunds_last_minute,
    
    -- Top stores (by sales)
    OBJECT_CONSTRUCT(
        'store_id', store_id,
        'sales_amount', SUM(total_amount)
    ) AS top_stores
FROM DEV_RAW.BRONZE.retail_events
WHERE event_timestamp >= CURRENT_TIMESTAMP() - INTERVAL '1 minute'
  AND event_type IN ('SALE', 'REFUND')
GROUP BY store_id
ORDER BY SUM(total_amount) DESC
LIMIT 10;

-- ============================================================================
-- Grant Permissions
-- ============================================================================

GRANT SELECT ON DYNAMIC TABLE DEV_DW.MART.dt_sales_by_store_minute TO ROLE DATA_ANALYST;
GRANT SELECT ON DYNAMIC TABLE DEV_DW.MART.dt_sales_by_store_hour TO ROLE DATA_ANALYST;
GRANT SELECT ON DYNAMIC TABLE DEV_DW.MART.dt_sales_by_store_day TO ROLE DATA_ANALYST;
GRANT SELECT ON DYNAMIC TABLE DEV_DW.MART.dt_realtime_dashboard TO ROLE DATA_ANALYST;


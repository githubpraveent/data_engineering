-- ============================================================================
-- Scenario B: Real-Time Aggregation with Dynamic Tables
-- Creates dynamic table for minute-level sales aggregation
-- ============================================================================

USE DATABASE DEV_DW;
USE SCHEMA MART;

-- ============================================================================
-- Dynamic Table: Minute-Level Sales Aggregation
-- Continuously updates aggregated metrics from POS events
-- ============================================================================

CREATE OR REPLACE DYNAMIC TABLE dt_sales_by_store_minute
  TARGET_LAG = '1 minute'  -- Update within 1 minute of source changes
  WAREHOUSE = WH_TRANS
AS
SELECT
    DATE_TRUNC('minute', transaction_timestamp) AS minute_timestamp,
    store_id,
    COUNT(DISTINCT transaction_id) AS transaction_count,
    COUNT(*) AS line_item_count,
    SUM(quantity) AS total_quantity,
    SUM(total_amount) AS total_sales_amount,
    AVG(total_amount) AS avg_transaction_amount,
    MIN(transaction_timestamp) AS first_transaction_in_minute,
    MAX(transaction_timestamp) AS last_transaction_in_minute
FROM DEV_RAW.BRONZE.pos_events
WHERE event_type = 'INSERT'  -- Only count sales, not refunds
GROUP BY
    DATE_TRUNC('minute', transaction_timestamp),
    store_id;

-- ============================================================================
-- Refresh the Dynamic Table (automatic, but can be manual)
-- ============================================================================

-- ALTER DYNAMIC TABLE dt_sales_by_store_minute REFRESH;

-- ============================================================================
-- Query the Dynamic Table
-- ============================================================================

-- SELECT * FROM dt_sales_by_store_minute
-- WHERE minute_timestamp >= CURRENT_TIMESTAMP() - INTERVAL '1 hour'
-- ORDER BY minute_timestamp DESC, store_id;

-- ============================================================================
-- Dynamic Table: Hourly Summary (for BI consumption)
-- ============================================================================

CREATE OR REPLACE DYNAMIC TABLE dt_sales_by_store_hour
  TARGET_LAG = '5 minutes'  -- Update within 5 minutes
  WAREHOUSE = WH_TRANS
AS
SELECT
    DATE_TRUNC('hour', minute_timestamp) AS hour_timestamp,
    store_id,
    SUM(transaction_count) AS total_transactions,
    SUM(line_item_count) AS total_line_items,
    SUM(total_quantity) AS total_quantity,
    SUM(total_sales_amount) AS total_sales_amount,
    AVG(avg_transaction_amount) AS avg_transaction_amount,
    MIN(first_transaction_in_minute) AS hour_start,
    MAX(last_transaction_in_minute) AS hour_end
FROM dt_sales_by_store_minute
GROUP BY
    DATE_TRUNC('hour', minute_timestamp),
    store_id;

-- ============================================================================
-- Grant Permissions
-- ============================================================================

GRANT SELECT ON DYNAMIC TABLE DEV_DW.MART.dt_sales_by_store_minute TO ROLE DATA_ANALYST;
GRANT SELECT ON DYNAMIC TABLE DEV_DW.MART.dt_sales_by_store_hour TO ROLE DATA_ANALYST;


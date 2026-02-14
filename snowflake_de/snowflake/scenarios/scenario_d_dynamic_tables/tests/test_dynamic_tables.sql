-- ============================================================================
-- Scenario D: Real-Time Aggregated Analytics - Test Scripts
-- Comprehensive tests for dynamic tables
-- ============================================================================

USE DATABASE DEV_DW;
USE SCHEMA MART;

-- ============================================================================
-- Test 1: Verify Dynamic Table Refresh
-- ============================================================================

SELECT 
    'Test 1: Dynamic Table Refresh Status' as test_name,
    TABLE_NAME,
    REFRESH_MODE,
    TARGET_LAG,
    LAST_REFRESH_TIME,
    DATEDIFF(second, LAST_REFRESH_TIME, CURRENT_TIMESTAMP()) as seconds_since_refresh
FROM INFORMATION_SCHEMA.DYNAMIC_TABLES
WHERE TABLE_SCHEMA = 'MART'
  AND TABLE_NAME LIKE 'DT_%'
ORDER BY LAST_REFRESH_TIME DESC;

-- Expected: seconds_since_refresh <= TARGET_LAG (within target latency)

-- ============================================================================
-- Test 2: Validate Aggregation Correctness
-- ============================================================================

-- Compare minute-level aggregation with source data
SELECT 
    'Test 2: Aggregation Correctness' as test_name,
    (SELECT SUM(CASE WHEN event_type = 'SALE' THEN total_amount ELSE 0 END)
     FROM DEV_RAW.BRONZE.retail_events
     WHERE event_timestamp >= CURRENT_TIMESTAMP() - INTERVAL '1 hour') as source_total_sales,
    (SELECT SUM(total_sales_amount)
     FROM dt_sales_by_store_minute
     WHERE minute_timestamp >= DATE_TRUNC('hour', CURRENT_TIMESTAMP() - INTERVAL '1 hour')) as aggregated_total_sales,
    ABS(
        (SELECT SUM(CASE WHEN event_type = 'SALE' THEN total_amount ELSE 0 END)
         FROM DEV_RAW.BRONZE.retail_events
         WHERE event_timestamp >= CURRENT_TIMESTAMP() - INTERVAL '1 hour') -
        (SELECT SUM(total_sales_amount)
         FROM dt_sales_by_store_minute
         WHERE minute_timestamp >= DATE_TRUNC('hour', CURRENT_TIMESTAMP() - INTERVAL '1 hour'))
    ) as difference;

-- Expected: difference should be minimal (within rounding tolerance)

-- ============================================================================
-- Test 3: Verify Hour-Level Aggregation
-- ============================================================================

SELECT 
    'Test 3: Hour-Level Aggregation' as test_name,
    (SELECT SUM(total_sales_amount)
     FROM dt_sales_by_store_minute
     WHERE minute_timestamp >= DATE_TRUNC('hour', CURRENT_TIMESTAMP() - INTERVAL '1 hour')) as minute_total,
    (SELECT SUM(total_sales_amount)
     FROM dt_sales_by_store_hour
     WHERE hour_timestamp >= DATE_TRUNC('hour', CURRENT_TIMESTAMP() - INTERVAL '1 hour')) as hour_total,
    ABS(
        (SELECT SUM(total_sales_amount)
         FROM dt_sales_by_store_minute
         WHERE minute_timestamp >= DATE_TRUNC('hour', CURRENT_TIMESTAMP() - INTERVAL '1 hour')) -
        (SELECT SUM(total_sales_amount)
         FROM dt_sales_by_store_hour
         WHERE hour_timestamp >= DATE_TRUNC('hour', CURRENT_TIMESTAMP() - INTERVAL '1 hour'))
    ) as difference;

-- Expected: difference should be 0 (hour aggregates from minutes)

-- ============================================================================
-- Test 4: Check for Data Gaps
-- ============================================================================

WITH minute_series AS (
    SELECT DATE_TRUNC('minute', event_timestamp) AS minute_timestamp
    FROM DEV_RAW.BRONZE.retail_events
    WHERE event_timestamp >= CURRENT_TIMESTAMP() - INTERVAL '24 hours'
    GROUP BY DATE_TRUNC('minute', event_timestamp)
)
SELECT 
    'Test 4: Data Gaps' as test_name,
    ms.minute_timestamp,
    CASE 
        WHEN dt.minute_timestamp IS NULL THEN 'MISSING'
        ELSE 'PRESENT'
    END as aggregation_status
FROM minute_series ms
LEFT JOIN dt_sales_by_store_minute dt
    ON ms.minute_timestamp = dt.minute_timestamp
WHERE dt.minute_timestamp IS NULL
LIMIT 10;

-- Expected: Most minutes should have aggregations (some gaps are acceptable)

-- ============================================================================
-- Test 5: Query Performance Test
-- ============================================================================

-- Test query performance on dynamic table vs source
SELECT 
    'Test 5: Query Performance' as test_name,
    'Dynamic Table' as table_type,
    COUNT(*) as row_count,
    MIN(minute_timestamp) as earliest_minute,
    MAX(minute_timestamp) as latest_minute
FROM dt_sales_by_store_minute
WHERE minute_timestamp >= CURRENT_TIMESTAMP() - INTERVAL '24 hours';

-- Compare with source query (should be much faster on dynamic table)
-- SELECT 
--     'Source Table' as table_type,
--     COUNT(*) as row_count
-- FROM (
--     SELECT DATE_TRUNC('minute', event_timestamp) AS minute_timestamp,
--            store_id, product_id, SUM(total_amount) as total
--     FROM DEV_RAW.BRONZE.retail_events
--     WHERE event_timestamp >= CURRENT_TIMESTAMP() - INTERVAL '24 hours'
--     GROUP BY DATE_TRUNC('minute', event_timestamp), store_id, product_id
-- );

-- ============================================================================
-- Test 6: Edge Cases - No Data
-- ============================================================================

-- Test behavior when no data exists (should return 0 rows or NULL)
SELECT 
    'Test 6: No Data Edge Case' as test_name,
    COUNT(*) as row_count
FROM dt_sales_by_store_minute
WHERE minute_timestamp >= CURRENT_TIMESTAMP() + INTERVAL '1 day';

-- Expected: row_count = 0

-- ============================================================================
-- Test 7: Edge Cases - Data Burst
-- ============================================================================

-- Simulate a burst of events and verify aggregation handles it
SELECT 
    'Test 7: Data Burst Handling' as test_name,
    minute_timestamp,
    COUNT(DISTINCT store_id) as stores_in_minute,
    COUNT(DISTINCT product_id) as products_in_minute,
    SUM(transaction_count) as transactions_in_minute,
    SUM(total_sales_amount) as sales_in_minute
FROM dt_sales_by_store_minute
WHERE minute_timestamp >= CURRENT_TIMESTAMP() - INTERVAL '1 hour'
GROUP BY minute_timestamp
HAVING SUM(transaction_count) > 1000  -- High transaction volume
ORDER BY SUM(transaction_count) DESC
LIMIT 10;

-- Expected: Aggregation should handle bursts without errors

-- ============================================================================
-- Test 8: Verify Updates (Incremental Processing)
-- ============================================================================

-- Verify that dynamic table updates when source data changes
SELECT 
    'Test 8: Update Verification' as test_name,
    LAST_REFRESH_TIME as last_refresh,
    CURRENT_TIMESTAMP() as current_time,
    DATEDIFF(second, LAST_REFRESH_TIME, CURRENT_TIMESTAMP()) as seconds_since_refresh,
    CASE 
        WHEN DATEDIFF(second, LAST_REFRESH_TIME, CURRENT_TIMESTAMP()) <= CAST(TARGET_LAG AS INT) * 60
        THEN 'WITHIN_TARGET'
        ELSE 'BEHIND_TARGET'
    END as refresh_status
FROM INFORMATION_SCHEMA.DYNAMIC_TABLES
WHERE TABLE_SCHEMA = 'MART'
  AND TABLE_NAME = 'DT_SALES_BY_STORE_MINUTE';

-- Expected: refresh_status = 'WITHIN_TARGET'

-- ============================================================================
-- Test 9: Comprehensive Quality Report
-- ============================================================================

SELECT 
    'Test 9: Comprehensive Quality Report' as report_type,
    CURRENT_TIMESTAMP() as report_timestamp,
    (SELECT COUNT(*) FROM DEV_RAW.BRONZE.retail_events 
     WHERE event_timestamp >= CURRENT_TIMESTAMP() - INTERVAL '1 hour') as source_events,
    (SELECT COUNT(*) FROM dt_sales_by_store_minute 
     WHERE minute_timestamp >= DATE_TRUNC('hour', CURRENT_TIMESTAMP() - INTERVAL '1 hour')) as minute_records,
    (SELECT COUNT(*) FROM dt_sales_by_store_hour 
     WHERE hour_timestamp >= DATE_TRUNC('hour', CURRENT_TIMESTAMP() - INTERVAL '1 hour')) as hour_records,
    (SELECT MAX(DATEDIFF(second, LAST_REFRESH_TIME, CURRENT_TIMESTAMP()))
     FROM INFORMATION_SCHEMA.DYNAMIC_TABLES
     WHERE TABLE_SCHEMA = 'MART') as max_refresh_lag_seconds,
    CASE 
        WHEN (SELECT MAX(DATEDIFF(second, LAST_REFRESH_TIME, CURRENT_TIMESTAMP()))
              FROM INFORMATION_SCHEMA.DYNAMIC_TABLES
              WHERE TABLE_SCHEMA = 'MART') <= 300
        THEN 'HEALTHY'
        ELSE 'DEGRADED'
    END as overall_status;


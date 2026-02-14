-- ============================================================================
-- Scenario A: Batch Data Ingestion - Test Scripts
-- Comprehensive tests for batch ingestion pipeline
-- ============================================================================

USE DATABASE DEV_RAW;
USE SCHEMA BRONZE;

-- ============================================================================
-- Test 1: Validate Number of Records After Load
-- ============================================================================

SELECT 
    'Test 1: Record Count Validation' as test_name,
    COUNT(*) as total_records,
    COUNT(DISTINCT transaction_id) as unique_transactions,
    COUNT(DISTINCT file_name) as files_loaded,
    MIN(load_timestamp) as earliest_load,
    MAX(load_timestamp) as latest_load
FROM raw_sales
WHERE DATE(load_timestamp) = CURRENT_DATE();

-- Expected: total_records > 0, unique_transactions > 0, files_loaded > 0

-- ============================================================================
-- Test 2: Check for Duplicate Transaction IDs
-- ============================================================================

SELECT 
    'Test 2: Duplicate Transaction Check' as test_name,
    transaction_id,
    product_id,
    COUNT(*) as duplicate_count,
    LISTAGG(DISTINCT file_name, ', ') WITHIN GROUP (ORDER BY file_name) as source_files
FROM raw_sales
WHERE DATE(load_timestamp) = CURRENT_DATE()
GROUP BY transaction_id, product_id
HAVING COUNT(*) > 1;

-- Expected: No rows returned (no duplicates)

-- ============================================================================
-- Test 3: Check for Null Critical Fields
-- ============================================================================

SELECT 
    'Test 3: Null Value Check' as test_name,
    COUNT(*) as total_rows,
    SUM(CASE WHEN transaction_id IS NULL THEN 1 ELSE 0 END) as null_transaction_id,
    SUM(CASE WHEN store_id IS NULL THEN 1 ELSE 0 END) as null_store_id,
    SUM(CASE WHEN product_id IS NULL THEN 1 ELSE 0 END) as null_product_id,
    SUM(CASE WHEN transaction_date IS NULL THEN 1 ELSE 0 END) as null_transaction_date,
    SUM(CASE WHEN quantity IS NULL THEN 1 ELSE 0 END) as null_quantity,
    SUM(CASE WHEN total_amount IS NULL THEN 1 ELSE 0 END) as null_total_amount,
    ROUND(SUM(CASE WHEN transaction_id IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as null_transaction_id_pct
FROM raw_sales
WHERE DATE(load_timestamp) = CURRENT_DATE();

-- Expected: All null counts = 0

-- ============================================================================
-- Test 4: Validate Data Types
-- ============================================================================

SELECT 
    'Test 4: Data Type Validation' as test_name,
    COUNT(*) as total_rows,
    SUM(CASE WHEN TRY_TO_NUMBER(transaction_id::VARCHAR) IS NOT NULL THEN 1 ELSE 0 END) as numeric_transaction_ids,
    SUM(CASE WHEN transaction_date < '2020-01-01' OR transaction_date > CURRENT_DATE() + 1 THEN 1 ELSE 0 END) as invalid_dates,
    SUM(CASE WHEN quantity <= 0 THEN 1 ELSE 0 END) as invalid_quantities,
    SUM(CASE WHEN unit_price < 0 THEN 1 ELSE 0 END) as negative_prices,
    SUM(CASE WHEN total_amount < 0 THEN 1 ELSE 0 END) as negative_amounts
FROM raw_sales
WHERE DATE(load_timestamp) = CURRENT_DATE();

-- Expected: invalid_dates = 0, invalid_quantities = 0, negative_prices = 0, negative_amounts = 0

-- ============================================================================
-- Test 5: Validate Calculation Logic
-- ============================================================================

SELECT 
    'Test 5: Calculation Validation' as test_name,
    COUNT(*) as total_rows,
    SUM(CASE 
        WHEN ABS(total_amount - ((quantity * unit_price) - discount_amount + tax_amount)) > 0.01 
        THEN 1 ELSE 0 
    END) as calculation_errors,
    AVG(ABS(total_amount - ((quantity * unit_price) - discount_amount + tax_amount))) as avg_calculation_diff
FROM raw_sales
WHERE DATE(load_timestamp) = CURRENT_DATE();

-- Expected: calculation_errors = 0 or very low

-- ============================================================================
-- Test 6: Warehouse Table Validation
-- ============================================================================

USE DATABASE DEV_DW;
USE SCHEMA FACTS;

SELECT 
    'Test 6: Warehouse Table Validation' as test_name,
    COUNT(*) as total_warehouse_records,
    COUNT(DISTINCT transaction_id) as unique_transactions,
    COUNT(DISTINCT store_id) as unique_stores,
    SUM(total_amount) as total_sales_amount,
    MIN(transaction_date) as earliest_transaction,
    MAX(transaction_date) as latest_transaction,
    MAX(load_timestamp) as latest_load
FROM warehouse_sales
WHERE DATE(load_timestamp) = CURRENT_DATE();

-- ============================================================================
-- Test 7: Deduplication Validation
-- ============================================================================

SELECT 
    'Test 7: Deduplication Check' as test_name,
    transaction_id,
    product_id,
    COUNT(*) as duplicate_count
FROM warehouse_sales
GROUP BY transaction_id, product_id
HAVING COUNT(*) > 1;

-- Expected: No rows returned (no duplicates in warehouse)

-- ============================================================================
-- Test 8: Data Reconciliation (Raw vs Warehouse)
-- ============================================================================

SELECT 
    'Test 8: Data Reconciliation' as test_name,
    (SELECT COUNT(*) FROM DEV_RAW.BRONZE.raw_sales WHERE DATE(load_timestamp) = CURRENT_DATE()) as raw_row_count,
    (SELECT COUNT(*) FROM warehouse_sales WHERE DATE(load_timestamp) = CURRENT_DATE()) as warehouse_row_count,
    (SELECT SUM(total_amount) FROM DEV_RAW.BRONZE.raw_sales WHERE DATE(load_timestamp) = CURRENT_DATE()) as raw_total_amount,
    (SELECT SUM(total_amount) FROM warehouse_sales WHERE DATE(load_timestamp) = CURRENT_DATE()) as warehouse_total_amount,
    ABS(
        (SELECT SUM(total_amount) FROM DEV_RAW.BRONZE.raw_sales WHERE DATE(load_timestamp) = CURRENT_DATE()) -
        (SELECT SUM(total_amount) FROM warehouse_sales WHERE DATE(load_timestamp) = CURRENT_DATE())
    ) as amount_difference
;

-- Expected: warehouse_row_count <= raw_row_count (after deduplication)
-- Expected: amount_difference should be small (within rounding tolerance)

-- ============================================================================
-- Test 9: Performance Metrics
-- ============================================================================

SELECT 
    'Test 9: Load Performance' as test_name,
    file_name,
    COUNT(*) as records_in_file,
    MIN(load_timestamp) as load_start,
    MAX(load_timestamp) as load_end,
    DATEDIFF(second, MIN(load_timestamp), MAX(load_timestamp)) as load_duration_seconds,
    ROUND(COUNT(*) / NULLIF(DATEDIFF(second, MIN(load_timestamp), MAX(load_timestamp)), 0), 2) as records_per_second
FROM raw_sales
WHERE DATE(load_timestamp) = CURRENT_DATE()
GROUP BY file_name
ORDER BY load_start DESC;

-- ============================================================================
-- Test 10: Comprehensive Quality Report
-- ============================================================================

SELECT 
    'Test 10: Comprehensive Quality Report' as report_type,
    CURRENT_TIMESTAMP() as report_timestamp,
    DATE(CURRENT_TIMESTAMP()) as report_date,
    (SELECT COUNT(*) FROM DEV_RAW.BRONZE.raw_sales WHERE DATE(load_timestamp) = CURRENT_DATE()) as raw_records,
    (SELECT COUNT(DISTINCT transaction_id) FROM DEV_RAW.BRONZE.raw_sales WHERE DATE(load_timestamp) = CURRENT_DATE()) as unique_transactions,
    (SELECT COUNT(*) FROM warehouse_sales WHERE DATE(load_timestamp) = CURRENT_DATE()) as warehouse_records,
    (SELECT SUM(CASE WHEN transaction_id IS NULL THEN 1 ELSE 0 END) FROM DEV_RAW.BRONZE.raw_sales WHERE DATE(load_timestamp) = CURRENT_DATE()) as null_transaction_ids,
    (SELECT SUM(CASE WHEN total_amount < 0 THEN 1 ELSE 0 END) FROM DEV_RAW.BRONZE.raw_sales WHERE DATE(load_timestamp) = CURRENT_DATE()) as negative_amounts,
    (SELECT COUNT(*) FROM (
        SELECT transaction_id, product_id, COUNT(*) 
        FROM warehouse_sales 
        GROUP BY transaction_id, product_id 
        HAVING COUNT(*) > 1
    )) as duplicate_count,
    CASE 
        WHEN (SELECT COUNT(*) FROM DEV_RAW.BRONZE.raw_sales WHERE DATE(load_timestamp) = CURRENT_DATE()) = 0 
        THEN 'FAILED - No data loaded'
        WHEN (SELECT SUM(CASE WHEN transaction_id IS NULL THEN 1 ELSE 0 END) FROM DEV_RAW.BRONZE.raw_sales WHERE DATE(load_timestamp) = CURRENT_DATE()) > 0 
        THEN 'FAILED - Null transaction IDs'
        WHEN (SELECT COUNT(*) FROM (
            SELECT transaction_id, product_id, COUNT(*) 
            FROM warehouse_sales 
            GROUP BY transaction_id, product_id 
            HAVING COUNT(*) > 1
        )) > 0 
        THEN 'FAILED - Duplicates in warehouse'
        ELSE 'PASSED'
    END as overall_status;


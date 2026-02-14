-- ============================================================================
-- Scenario C: Historical Data + CDC with SCD Type 2 Dimensions - Tests
-- Comprehensive tests for SCD Type 2 dimension load
-- ============================================================================

USE DATABASE DEV_DW;
USE SCHEMA DIMENSIONS;

-- ============================================================================
-- Test 1: Validate SCD Type 2 Structure
-- ============================================================================

SELECT 
    'Test 1: SCD Type 2 Structure' as test_name,
    COUNT(*) as total_records,
    SUM(CASE WHEN is_current = TRUE THEN 1 ELSE 0 END) as current_records,
    SUM(CASE WHEN is_current = FALSE THEN 1 ELSE 0 END) as historical_records,
    SUM(CASE WHEN effective_to_date IS NULL THEN 1 ELSE 0 END) as null_effective_to,
    SUM(CASE WHEN effective_from_date > COALESCE(effective_to_date, '9999-12-31'::DATE) THEN 1 ELSE 0 END) as invalid_date_ranges
FROM dim_customers_scd2;

-- Expected: invalid_date_ranges = 0

-- ============================================================================
-- Test 2: One Current Record Per Customer
-- ============================================================================

SELECT 
    'Test 2: One Current Record Per Customer' as test_name,
    customer_id,
    COUNT(*) as current_record_count
FROM dim_customers_scd2
WHERE is_current = TRUE
GROUP BY customer_id
HAVING COUNT(*) != 1;

-- Expected: No rows returned (each customer has exactly one current record)

-- ============================================================================
-- Test 3: No Overlapping Effective Dates
-- ============================================================================

SELECT 
    'Test 3: Overlapping Effective Dates' as test_name,
    dc1.customer_id,
    dc1.effective_from_date as range1_start,
    dc1.effective_to_date as range1_end,
    dc2.effective_from_date as range2_start,
    dc2.effective_to_date as range2_end
FROM dim_customers_scd2 dc1
INNER JOIN dim_customers_scd2 dc2
    ON dc1.customer_id = dc2.customer_id
    AND dc1.customer_key != dc2.customer_key
    AND (
        -- Check for overlaps
        (dc1.effective_from_date BETWEEN dc2.effective_from_date 
         AND COALESCE(dc2.effective_to_date, '9999-12-31'::DATE))
        OR (COALESCE(dc1.effective_to_date, '9999-12-31'::DATE) BETWEEN dc2.effective_from_date 
            AND COALESCE(dc2.effective_to_date, '9999-12-31'::DATE))
    );

-- Expected: No rows returned (no overlapping effective dates)

-- ============================================================================
-- Test 4: Validate Effective Date Continuity
-- ============================================================================

SELECT 
    'Test 4: Effective Date Continuity' as test_name,
    dc1.customer_id,
    dc1.effective_to_date as previous_end,
    dc2.effective_from_date as next_start,
    DATEDIFF(day, dc1.effective_to_date, dc2.effective_from_date) as gap_days
FROM dim_customers_scd2 dc1
INNER JOIN dim_customers_scd2 dc2
    ON dc1.customer_id = dc2.customer_id
    AND dc1.effective_to_date IS NOT NULL
    AND dc2.effective_from_date > dc1.effective_from_date
    AND DATEDIFF(day, dc1.effective_to_date, dc2.effective_from_date) != 1
ORDER BY dc1.customer_id, dc1.effective_from_date;

-- Expected: gap_days = 1 for all records (continuous date ranges)

-- ============================================================================
-- Test 5: Simulate Updates and Validate
-- ============================================================================

-- Insert test customer
INSERT INTO DEV_RAW.BRONZE.raw_customers (
    customer_id, first_name, last_name, email, customer_segment
) VALUES (
    'TEST_CUST_001', 'John', 'Doe', 'john.doe@test.com', 'PREMIUM'
);

-- Run the merge procedure
CALL DEV_DW.DIMENSIONS.sp_load_customer_scd2_from_stream();

-- Validate: Should have 1 current record
SELECT 
    'Test 5a: Initial Insert' as test_name,
    COUNT(*) as record_count,
    SUM(CASE WHEN is_current = TRUE THEN 1 ELSE 0 END) as current_count
FROM dim_customers_scd2
WHERE customer_id = 'TEST_CUST_001';

-- Expected: record_count = 1, current_count = 1

-- Update customer
UPDATE DEV_RAW.BRONZE.raw_customers
SET email = 'john.doe.updated@test.com', customer_segment = 'VIP'
WHERE customer_id = 'TEST_CUST_001';

-- Run the merge procedure again
CALL DEV_DW.DIMENSIONS.sp_load_customer_scd2_from_stream();

-- Validate: Should have 2 records (1 historical, 1 current)
SELECT 
    'Test 5b: After Update' as test_name,
    COUNT(*) as record_count,
    SUM(CASE WHEN is_current = TRUE THEN 1 ELSE 0 END) as current_count,
    SUM(CASE WHEN is_current = FALSE THEN 1 ELSE 0 END) as historical_count,
    MAX(CASE WHEN is_current = TRUE THEN email END) as current_email,
    MAX(CASE WHEN is_current = FALSE THEN email END) as historical_email
FROM dim_customers_scd2
WHERE customer_id = 'TEST_CUST_001';

-- Expected: record_count = 2, current_count = 1, historical_count = 1
-- Expected: current_email = 'john.doe.updated@test.com'
-- Expected: historical_email = 'john.doe@test.com'

-- Delete customer
DELETE FROM DEV_RAW.BRONZE.raw_customers
WHERE customer_id = 'TEST_CUST_001';

-- Run the merge procedure again
CALL DEV_DW.DIMENSIONS.sp_load_customer_scd2_from_stream();

-- Validate: Should have 2 records (both historical, none current)
SELECT 
    'Test 5c: After Delete' as test_name,
    COUNT(*) as record_count,
    SUM(CASE WHEN is_current = TRUE THEN 1 ELSE 0 END) as current_count,
    SUM(CASE WHEN customer_status = 'INACTIVE' THEN 1 ELSE 0 END) as inactive_count
FROM dim_customers_scd2
WHERE customer_id = 'TEST_CUST_001';

-- Expected: record_count = 2, current_count = 0, inactive_count = 2

-- Clean up test data
DELETE FROM DEV_RAW.BRONZE.raw_customers WHERE customer_id = 'TEST_CUST_001';
DELETE FROM dim_customers_scd2 WHERE customer_id = 'TEST_CUST_001';

-- ============================================================================
-- Test 6: Time Travel Validation
-- ============================================================================

-- Test that historical versions can be queried
SELECT 
    'Test 6: Time Travel' as test_name,
    COUNT(*) as historical_versions,
    COUNT(DISTINCT customer_id) as unique_customers,
    MIN(effective_from_date) as earliest_date,
    MAX(effective_from_date) as latest_date
FROM dim_customers_scd2
AT (OFFSET => -86400)  -- 1 day ago
WHERE customer_id IN (
    SELECT DISTINCT customer_id 
    FROM dim_customers_scd2 
    LIMIT 10
);

-- ============================================================================
-- Test 7: Backfill Validation
-- ============================================================================

-- Test ability to backfill historical data
SELECT 
    'Test 7: Backfill Capability' as test_name,
    customer_id,
    COUNT(*) as version_count,
    MIN(effective_from_date) as first_version,
    MAX(effective_from_date) as latest_version,
    CASE 
        WHEN COUNT(*) > 1 THEN 'MULTIPLE_VERSIONS'
        ELSE 'SINGLE_VERSION'
    END as version_status
FROM dim_customers_scd2
WHERE registration_date >= '2020-01-01'
  AND registration_date <= '2024-12-31'
GROUP BY customer_id
HAVING COUNT(*) > 1
ORDER BY version_count DESC
LIMIT 10;


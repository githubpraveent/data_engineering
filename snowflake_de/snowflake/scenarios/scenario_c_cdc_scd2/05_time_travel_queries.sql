-- ============================================================================
-- Scenario C: Historical Data + CDC with SCD Type 2 Dimensions
-- Time Travel queries for auditing and debugging
-- ============================================================================

USE DATABASE DEV_DW;
USE SCHEMA DIMENSIONS;

-- ============================================================================
-- Query Historical Versions of Customer Data
-- ============================================================================

-- Query customer dimension as it was 1 day ago
SELECT 
    customer_id,
    first_name,
    last_name,
    email,
    effective_from_date,
    effective_to_date,
    is_current
FROM dim_customers_scd2
AT (OFFSET => -86400)  -- 1 day ago (in seconds)
WHERE customer_id = 'CUST001'
ORDER BY effective_from_date;

-- Query customer dimension at a specific timestamp
SELECT 
    customer_id,
    first_name,
    last_name,
    email,
    effective_from_date,
    effective_to_date,
    is_current
FROM dim_customers_scd2
AT (TIMESTAMP => '2024-01-15 10:00:00'::TIMESTAMP_NTZ)
WHERE customer_id = 'CUST001'
ORDER BY effective_from_date;

-- Query customer dimension at a specific statement ID
-- SELECT 
--     customer_id,
--     first_name,
--     last_name,
--     email
-- FROM dim_customers_scd2
-- AT (STATEMENT => 'statement_id_here')
-- WHERE customer_id = 'CUST001';

-- ============================================================================
-- Compare Current vs Historical
-- ============================================================================

-- Compare current customer record with historical record (1 day ago)
SELECT 
    'CURRENT' as version,
    customer_id,
    first_name,
    last_name,
    email,
    address_line1,
    customer_segment,
    effective_from_date,
    effective_to_date,
    is_current
FROM dim_customers_scd2
WHERE customer_id = 'CUST001'
  AND is_current = TRUE

UNION ALL

SELECT 
    'HISTORICAL' as version,
    customer_id,
    first_name,
    last_name,
    email,
    address_line1,
    customer_segment,
    effective_from_date,
    effective_to_date,
    is_current
FROM dim_customers_scd2
AT (OFFSET => -86400)  -- 1 day ago
WHERE customer_id = 'CUST001'
  AND is_current = TRUE
ORDER BY version, effective_from_date;

-- ============================================================================
-- Audit Trail: Track All Changes to a Customer
-- ============================================================================

SELECT 
    customer_id,
    first_name,
    last_name,
    email,
    customer_segment,
    effective_from_date,
    effective_to_date,
    is_current,
    created_at,
    updated_at,
    DATEDIFF(day, effective_from_date, COALESCE(effective_to_date, CURRENT_DATE())) as days_active
FROM dim_customers_scd2
WHERE customer_id = 'CUST001'
ORDER BY effective_from_date;

-- ============================================================================
-- Find Customers That Changed in a Date Range
-- ============================================================================

SELECT 
    customer_id,
    COUNT(*) as version_count,
    MIN(effective_from_date) as first_version_date,
    MAX(effective_from_date) as latest_version_date,
    SUM(CASE WHEN is_current = TRUE THEN 1 ELSE 0 END) as current_version_exists
FROM dim_customers_scd2
WHERE effective_from_date >= '2024-01-01'
  AND effective_from_date <= CURRENT_DATE()
GROUP BY customer_id
HAVING COUNT(*) > 1  -- Only customers with multiple versions
ORDER BY version_count DESC;

-- ============================================================================
-- Backup and Restore Example
-- ============================================================================

-- Create a clone of the dimension at a specific point in time
-- CREATE OR REPLACE TABLE dim_customers_scd2_backup_20240115
-- CLONE dim_customers_scd2
-- AT (TIMESTAMP => '2024-01-15 23:59:59'::TIMESTAMP_NTZ);

-- Restore from backup (example)
-- CREATE OR REPLACE TABLE dim_customers_scd2_restored
-- CLONE dim_customers_scd2_backup_20240115;

-- ============================================================================
-- Query Deleted Records (using Time Travel)
-- ============================================================================

-- Find customers that were deleted (no longer in current table but existed before)
SELECT 
    dc_historical.customer_id,
    dc_historical.first_name,
    dc_historical.last_name,
    dc_historical.email,
    dc_historical.customer_status,
    dc_historical.effective_to_date,
    dc_historical.updated_at as deleted_at
FROM dim_customers_scd2 AT (OFFSET => -86400) dc_historical
WHERE dc_historical.customer_id NOT IN (
    SELECT customer_id 
    FROM dim_customers_scd2 
    WHERE is_current = TRUE
)
  AND dc_historical.is_current = TRUE
  AND dc_historical.customer_status = 'INACTIVE';


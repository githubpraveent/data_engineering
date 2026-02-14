-- ============================================================================
-- Data Quality Test Queries
-- These queries can be run manually or integrated into testing framework
-- ============================================================================

-- ============================================================================
-- Test 1: Completeness - Check for NULL values in critical fields
-- ============================================================================

SELECT 
    'raw_pos' as table_name,
    COUNT(*) as total_rows,
    SUM(CASE WHEN transaction_id IS NULL THEN 1 ELSE 0 END) as null_transaction_id,
    SUM(CASE WHEN store_id IS NULL THEN 1 ELSE 0 END) as null_store_id,
    SUM(CASE WHEN product_id IS NULL THEN 1 ELSE 0 END) as null_product_id,
    ROUND(SUM(CASE WHEN transaction_id IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as null_transaction_id_pct
FROM DEV_RAW.BRONZE.raw_pos
WHERE load_timestamp >= CURRENT_TIMESTAMP() - INTERVAL '24 hours';

-- ============================================================================
-- Test 2: Accuracy - Check for negative or invalid amounts
-- ============================================================================

SELECT 
    'stg_pos' as table_name,
    COUNT(*) as total_rows,
    SUM(CASE WHEN total_amount < 0 THEN 1 ELSE 0 END) as negative_amounts,
    SUM(CASE WHEN unit_price < 0 THEN 1 ELSE 0 END) as negative_prices,
    SUM(CASE WHEN quantity <= 0 THEN 1 ELSE 0 END) as invalid_quantities
FROM DEV_STAGING.SILVER.stg_pos
WHERE created_at >= CURRENT_TIMESTAMP() - INTERVAL '24 hours';

-- ============================================================================
-- Test 3: Consistency - Check referential integrity
-- ============================================================================

SELECT 
    'fact_sales' as fact_table,
    COUNT(*) as orphaned_records,
    SUM(CASE WHEN dp.product_key IS NULL THEN 1 ELSE 0 END) as missing_product,
    SUM(CASE WHEN ds.store_key IS NULL THEN 1 ELSE 0 END) as missing_store,
    SUM(CASE WHEN dd.date_key IS NULL THEN 1 ELSE 0 END) as missing_date
FROM DEV_DW.FACTS.fact_sales fs
LEFT JOIN DEV_DW.DIMENSIONS.dim_product dp ON fs.product_key = dp.product_key
LEFT JOIN DEV_DW.DIMENSIONS.dim_store ds ON fs.store_key = ds.store_key
LEFT JOIN DEV_DW.DIMENSIONS.dim_date dd ON fs.date_key = dd.date_key
WHERE dp.product_key IS NULL 
   OR ds.store_key IS NULL 
   OR dd.date_key IS NULL;

-- ============================================================================
-- Test 4: Timeliness - Check data freshness
-- ============================================================================

SELECT 
    'raw_pos' as table_name,
    MAX(load_timestamp) as latest_load,
    DATEDIFF(hour, MAX(load_timestamp), CURRENT_TIMESTAMP()) as hours_since_last_load,
    CASE 
        WHEN DATEDIFF(hour, MAX(load_timestamp), CURRENT_TIMESTAMP()) > 2 THEN 'STALE'
        ELSE 'FRESH'
    END as freshness_status
FROM DEV_RAW.BRONZE.raw_pos;

-- ============================================================================
-- Test 5: Uniqueness - Check for duplicate transactions
-- ============================================================================

SELECT 
    transaction_id,
    product_id,
    COUNT(*) as duplicate_count
FROM DEV_STAGING.SILVER.stg_pos
GROUP BY transaction_id, product_id
HAVING COUNT(*) > 1;

-- ============================================================================
-- Test 6: Business Rules - Validate calculation logic
-- ============================================================================

SELECT 
    'stg_pos' as table_name,
    COUNT(*) as total_rows,
    SUM(CASE 
        WHEN ABS(total_amount - ((quantity * unit_price) - discount_amount + tax_amount)) > 0.01 
        THEN 1 ELSE 0 
    END) as calculation_errors
FROM DEV_STAGING.SILVER.stg_pos
WHERE created_at >= CURRENT_TIMESTAMP() - INTERVAL '24 hours';

-- ============================================================================
-- Test 7: Range Checks - Check for unrealistic values
-- ============================================================================

SELECT 
    'stg_pos' as table_name,
    COUNT(*) as total_rows,
    SUM(CASE WHEN unit_price > 100000 THEN 1 ELSE 0 END) as unrealistic_prices,
    SUM(CASE WHEN quantity > 10000 THEN 1 ELSE 0 END) as unrealistic_quantities,
    SUM(CASE WHEN total_amount > 1000000 THEN 1 ELSE 0 END) as unrealistic_totals
FROM DEV_STAGING.SILVER.stg_pos
WHERE created_at >= CURRENT_TIMESTAMP() - INTERVAL '24 hours';

-- ============================================================================
-- Test 8: SCD Type 2 Validation - Check for overlapping effective dates
-- ============================================================================

SELECT 
    customer_id,
    COUNT(*) as overlapping_records
FROM (
    SELECT 
        dc1.customer_id,
        dc1.effective_from_date,
        dc1.effective_to_date
    FROM DEV_DW.DIMENSIONS.dim_customer dc1
    INNER JOIN DEV_DW.DIMENSIONS.dim_customer dc2
        ON dc1.customer_id = dc2.customer_id
        AND dc1.customer_key != dc2.customer_key
        AND (
            (dc1.effective_from_date BETWEEN dc2.effective_from_date AND COALESCE(dc2.effective_to_date, '9999-12-31'))
            OR (COALESCE(dc1.effective_to_date, '9999-12-31') BETWEEN dc2.effective_from_date AND COALESCE(dc2.effective_to_date, '9999-12-31'))
        )
) overlapping
GROUP BY customer_id
HAVING COUNT(*) > 0;

-- ============================================================================
-- Test 9: Data Volume - Check for unexpected drops in volume
-- ============================================================================

SELECT 
    DATE(load_timestamp) as load_date,
    COUNT(*) as row_count,
    LAG(COUNT(*)) OVER (ORDER BY DATE(load_timestamp)) as previous_day_count,
    ROUND((COUNT(*) - LAG(COUNT(*)) OVER (ORDER BY DATE(load_timestamp))) * 100.0 / 
          NULLIF(LAG(COUNT(*)) OVER (ORDER BY DATE(load_timestamp)), 0), 2) as pct_change
FROM DEV_RAW.BRONZE.raw_pos
WHERE load_timestamp >= CURRENT_TIMESTAMP() - INTERVAL '7 days'
GROUP BY DATE(load_timestamp)
ORDER BY load_date DESC;

-- ============================================================================
-- Test 10: Data Quality Summary Report
-- ============================================================================

SELECT 
    'Data Quality Summary' as report_type,
    CURRENT_TIMESTAMP() as report_timestamp,
    (SELECT COUNT(*) FROM DEV_RAW.BRONZE.raw_pos WHERE load_timestamp >= CURRENT_TIMESTAMP() - INTERVAL '24 hours') as raw_pos_rows,
    (SELECT COUNT(*) FROM DEV_STAGING.SILVER.stg_pos WHERE created_at >= CURRENT_TIMESTAMP() - INTERVAL '24 hours') as stg_pos_rows,
    (SELECT COUNT(*) FROM DEV_DW.FACTS.fact_sales WHERE created_at >= CURRENT_TIMESTAMP() - INTERVAL '24 hours') as fact_sales_rows,
    (SELECT SUM(CASE WHEN is_valid = FALSE THEN 1 ELSE 0 END) FROM DEV_STAGING.SILVER.stg_pos WHERE created_at >= CURRENT_TIMESTAMP() - INTERVAL '24 hours') as invalid_rows;


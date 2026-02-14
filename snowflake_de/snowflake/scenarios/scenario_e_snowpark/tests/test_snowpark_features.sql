-- ============================================================================
-- Scenario E: Data Engineering With Snowpark - Test Scripts
-- Comprehensive tests for Snowpark feature engineering
-- ============================================================================

USE DATABASE DEV_DW;
USE SCHEMA MART;

-- ============================================================================
-- Test 1: Validate Feature Table Structure
-- ============================================================================

SELECT 
    'Test 1: Feature Table Structure' as test_name,
    COUNT(*) as total_customers,
    SUM(CASE WHEN customer_ltv IS NULL THEN 1 ELSE 0 END) as null_ltv,
    SUM(CASE WHEN avg_order_value IS NULL THEN 1 ELSE 0 END) as null_avg_order,
    SUM(CASE WHEN total_transactions IS NULL THEN 1 ELSE 0 END) as null_transactions,
    MIN(customer_ltv) as min_ltv,
    MAX(customer_ltv) as max_ltv,
    AVG(customer_ltv) as avg_ltv
FROM customer_features;

-- Expected: null_ltv = 0, null_avg_order = 0, null_transactions = 0

-- ============================================================================
-- Test 2: Validate LTV Calculation
-- ============================================================================

-- Compare computed LTV with source data
SELECT 
    'Test 2: LTV Calculation Validation' as test_name,
    cf.customer_id,
    cf.customer_ltv as computed_ltv,
    (SELECT SUM(total_amount) 
     FROM DEV_RAW.BRONZE.pos_events 
     WHERE customer_id = cf.customer_id) as source_ltv,
    ABS(cf.customer_ltv - (SELECT SUM(total_amount) 
                           FROM DEV_RAW.BRONZE.pos_events 
                           WHERE customer_id = cf.customer_id)) as ltv_difference
FROM customer_features cf
WHERE ABS(cf.customer_ltv - (SELECT SUM(total_amount) 
                             FROM DEV_RAW.BRONZE.pos_events 
                             WHERE customer_id = cf.customer_id)) > 0.01
LIMIT 10;

-- Expected: ltv_difference should be minimal (within rounding tolerance)

-- ============================================================================
-- Test 3: Validate RFM Scores
-- ============================================================================

SELECT 
    'Test 3: RFM Score Validation' as test_name,
    COUNT(*) as total_customers,
    SUM(CASE WHEN recency_score BETWEEN 1 AND 5 THEN 1 ELSE 0 END) as valid_recency_scores,
    SUM(CASE WHEN frequency_score BETWEEN 1 AND 5 THEN 1 ELSE 0 END) as valid_frequency_scores,
    SUM(CASE WHEN monetary_score BETWEEN 1 AND 5 THEN 1 ELSE 0 END) as valid_monetary_scores,
    SUM(CASE WHEN rfm_score BETWEEN 111 AND 555 THEN 1 ELSE 0 END) as valid_rfm_scores,
    COUNT(DISTINCT customer_segment) as distinct_segments
FROM customer_features;

-- Expected: All scores should be within valid ranges

-- ============================================================================
-- Test 4: Validate Feature Idempotency
-- ============================================================================

-- Run feature computation twice and compare results
-- This test should be run manually:
-- 1. Call sp_compute_customer_features()
-- 2. Capture results
-- 3. Call sp_compute_customer_features() again
-- 4. Compare results (should be identical for same input data)

SELECT 
    'Test 4: Feature Idempotency' as test_name,
    'Run stored procedure twice and compare results manually' as test_instruction;

-- ============================================================================
-- Test 5: Validate Incremental Processing
-- ============================================================================

-- Test that incremental processing only updates changed customers
SELECT 
    'Test 5: Incremental Processing' as test_name,
    (SELECT COUNT(*) FROM DEV_STAGING.STREAMS.stream_customer_changes) as changed_customers,
    (SELECT COUNT(DISTINCT customer_id) FROM customer_features 
     WHERE updated_at >= CURRENT_TIMESTAMP() - INTERVAL '1 hour') as recently_updated_customers
;

-- Expected: recently_updated_customers <= changed_customers

-- ============================================================================
-- Test 6: Validate Backfill Capability
-- ============================================================================

-- Test that features can be computed for historical periods
SELECT 
    'Test 6: Backfill Capability' as test_name,
    COUNT(*) as historical_features,
    MIN(historical_period_start) as earliest_period,
    MAX(historical_period_end) as latest_period
FROM customer_features_historical
WHERE computation_timestamp >= CURRENT_TIMESTAMP() - INTERVAL '7 days';

-- Expected: historical_features > 0 if backfill was run

-- ============================================================================
-- Test 7: Validate Feature Completeness
-- ============================================================================

-- Check that all customers with transactions have features
SELECT 
    'Test 7: Feature Completeness' as test_name,
    (SELECT COUNT(DISTINCT customer_id) 
     FROM DEV_RAW.BRONZE.pos_events 
     WHERE customer_id IS NOT NULL) as customers_with_transactions,
    (SELECT COUNT(DISTINCT customer_id) 
     FROM customer_features) as customers_with_features,
    (SELECT COUNT(DISTINCT customer_id) 
     FROM DEV_RAW.BRONZE.pos_events 
     WHERE customer_id IS NOT NULL) -
    (SELECT COUNT(DISTINCT customer_id) 
     FROM customer_features) as missing_features
;

-- Expected: missing_features should be 0 or minimal

-- ============================================================================
-- Test 8: Validate Feature Quality
-- ============================================================================

SELECT 
    'Test 8: Feature Quality' as test_name,
    COUNT(*) as total_customers,
    SUM(CASE WHEN customer_ltv < 0 THEN 1 ELSE 0 END) as negative_ltv,
    SUM(CASE WHEN avg_order_value < 0 THEN 1 ELSE 0 END) as negative_avg_order,
    SUM(CASE WHEN total_transactions < 0 THEN 1 ELSE 0 END) as negative_transactions,
    SUM(CASE WHEN purchase_frequency < 0 THEN 1 ELSE 0 END) as negative_frequency,
    SUM(CASE WHEN customer_ltv > 1000000 THEN 1 ELSE 0 END) as unrealistic_high_ltv
FROM customer_features;

-- Expected: All negative counts should be 0

-- ============================================================================
-- Test 9: Performance Test
-- ============================================================================

-- Test query performance on feature table
SELECT 
    'Test 9: Query Performance' as test_name,
    COUNT(*) as feature_count,
    AVG(customer_ltv) as avg_ltv,
    MAX(customer_ltv) as max_ltv,
    MIN(customer_ltv) as min_ltv
FROM customer_features
WHERE ltv_segment = 'HIGH'
  AND customer_segment IN ('Champions', 'Loyal Customers');

-- Expected: Query should complete quickly (< 5 seconds for reasonable data volume)

-- ============================================================================
-- Test 10: Comprehensive Quality Report
-- ============================================================================

SELECT 
    'Test 10: Comprehensive Quality Report' as report_type,
    CURRENT_TIMESTAMP() as report_timestamp,
    (SELECT COUNT(*) FROM customer_features) as total_customers,
    (SELECT COUNT(*) FROM customer_features WHERE customer_ltv IS NOT NULL) as customers_with_ltv,
    (SELECT COUNT(*) FROM customer_features WHERE rfm_score IS NOT NULL) as customers_with_rfm,
    (SELECT COUNT(DISTINCT customer_segment) FROM customer_features) as distinct_segments,
    (SELECT AVG(customer_ltv) FROM customer_features) as avg_ltv,
    (SELECT AVG(total_transactions) FROM customer_features) as avg_transactions,
    (SELECT MAX(updated_at) FROM customer_features) as last_update_time,
    CASE 
        WHEN (SELECT COUNT(*) FROM customer_features) = 0 THEN 'FAILED - No features computed'
        WHEN (SELECT SUM(CASE WHEN customer_ltv IS NULL THEN 1 ELSE 0 END) FROM customer_features) > 0 THEN 'FAILED - Null LTV values'
        WHEN (SELECT MAX(updated_at) FROM customer_features) < CURRENT_TIMESTAMP() - INTERVAL '2 days' THEN 'WARNING - Features may be stale'
        ELSE 'PASSED'
    END as overall_status;


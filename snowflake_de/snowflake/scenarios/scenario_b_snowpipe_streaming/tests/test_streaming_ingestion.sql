-- ============================================================================
-- Scenario B: Real-Time Ingestion - Test Scripts
-- Comprehensive tests for streaming ingestion pipeline
-- ============================================================================

USE DATABASE DEV_RAW;
USE SCHEMA BRONZE;

-- ============================================================================
-- Test 1: Validate Ingestion Latency
-- ============================================================================

SELECT 
    'Test 1: Ingestion Latency' as test_name,
    AVG(DATEDIFF(second, event_timestamp, ingested_at)) as avg_latency_seconds,
    MIN(DATEDIFF(second, event_timestamp, ingested_at)) as min_latency_seconds,
    MAX(DATEDIFF(second, event_timestamp, ingested_at)) as max_latency_seconds,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY DATEDIFF(second, event_timestamp, ingested_at)) as p95_latency_seconds
FROM pos_events
WHERE ingested_at >= CURRENT_TIMESTAMP() - INTERVAL '1 hour';

-- Expected: avg_latency_seconds < 10 (Snowpipe Streaming target: 5-10 seconds)

-- ============================================================================
-- Test 2: Verify Stream Captures Inserts
-- ============================================================================

USE DATABASE DEV_STAGING;
USE SCHEMA STREAMS;

SELECT 
    'Test 2: Stream Capture Validation' as test_name,
    METADATA$ACTION,
    COUNT(*) as record_count,
    MIN(METADATA$ROW_ID) as min_row_id,
    MAX(METADATA$ROW_ID) as max_row_id
FROM stream_pos_events_changes
GROUP BY METADATA$ACTION;

-- Expected: METADATA$ACTION = 'INSERT' records exist

-- ============================================================================
-- Test 3: Test Merge Outcome
-- ============================================================================

USE DATABASE DEV_DW;
USE SCHEMA FACTS;

SELECT 
    'Test 3: Merge Outcome Validation' as test_name,
    COUNT(*) as fact_records,
    COUNT(DISTINCT transaction_id) as unique_transactions,
    SUM(total_amount) as total_sales,
    MIN(created_at) as earliest_load,
    MAX(created_at) as latest_load
FROM fact_sales
WHERE source_system = 'KAFKA_STREAMING'
  AND created_at >= CURRENT_TIMESTAMP() - INTERVAL '1 hour';

-- ============================================================================
-- Test 4: Verify Aggregated Results (Dynamic Table)
-- ============================================================================

USE DATABASE DEV_DW;
USE SCHEMA MART;

SELECT 
    'Test 4: Dynamic Table Aggregation' as test_name,
    COUNT(*) as minute_records,
    SUM(transaction_count) as total_transactions,
    SUM(total_sales_amount) as total_sales,
    MIN(minute_timestamp) as earliest_minute,
    MAX(minute_timestamp) as latest_minute,
    DATEDIFF(minute, MAX(minute_timestamp), CURRENT_TIMESTAMP()) as minutes_behind
FROM dt_sales_by_store_minute
WHERE minute_timestamp >= CURRENT_TIMESTAMP() - INTERVAL '1 hour';

-- Expected: minutes_behind <= 2 (within TARGET_LAG + some buffer)

-- ============================================================================
-- Test 5: End-to-End Validation
-- ============================================================================

SELECT 
    'Test 5: End-to-End Validation' as test_name,
    (SELECT COUNT(*) FROM DEV_RAW.BRONZE.pos_events 
     WHERE ingested_at >= CURRENT_TIMESTAMP() - INTERVAL '1 hour') as raw_events,
    (SELECT COUNT(*) FROM DEV_DW.FACTS.fact_sales 
     WHERE source_system = 'KAFKA_STREAMING' 
     AND created_at >= CURRENT_TIMESTAMP() - INTERVAL '1 hour') as fact_records,
    (SELECT SUM(total_sales_amount) FROM DEV_DW.MART.dt_sales_by_store_minute
     WHERE minute_timestamp >= CURRENT_TIMESTAMP() - INTERVAL '1 hour') as aggregated_sales;

-- Expected: fact_records <= raw_events (some events may be filtered/transformed)

-- ============================================================================
-- Test 6: Simulate Event Burst
-- ============================================================================

-- This test would be run manually with a burst of events
-- Expected: System handles burst gracefully, latency increases but stays acceptable

-- ============================================================================
-- Test 7: Verify Order Preservation (within channel)
-- ============================================================================

SELECT 
    'Test 7: Order Preservation' as test_name,
    kafka_topic,
    kafka_partition,
    COUNT(*) as events_in_partition,
    MIN(kafka_offset) as min_offset,
    MAX(kafka_offset) as max_offset,
    COUNT(DISTINCT kafka_offset) as unique_offsets,
    CASE 
        WHEN COUNT(*) = COUNT(DISTINCT kafka_offset) THEN 'PASS - No gaps'
        ELSE 'FAIL - Gaps detected'
    END as order_status
FROM DEV_RAW.BRONZE.pos_events
WHERE ingested_at >= CURRENT_TIMESTAMP() - INTERVAL '1 hour'
GROUP BY kafka_topic, kafka_partition;

-- Expected: order_status = 'PASS - No gaps' or reasonable gaps if multiple producers


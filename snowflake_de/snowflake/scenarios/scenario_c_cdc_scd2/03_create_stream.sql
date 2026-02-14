-- ============================================================================
-- Scenario C: Historical Data + CDC with SCD Type 2 Dimensions
-- Creates stream to capture changes on raw_customers table
-- ============================================================================

USE DATABASE DEV_STAGING;
USE SCHEMA STREAMS;

-- ============================================================================
-- Stream: Customer Changes
-- ============================================================================

CREATE OR REPLACE STREAM stream_customer_changes
ON TABLE DEV_RAW.BRONZE.raw_customers
COMMENT = 'Stream to capture changes in raw_customers for SCD Type 2 processing';

-- ============================================================================
-- Grant Permissions
-- ============================================================================

GRANT SELECT ON STREAM DEV_STAGING.STREAMS.stream_customer_changes TO ROLE DATA_ENGINEER;

-- ============================================================================
-- Check Stream Status
-- ============================================================================

-- SELECT SYSTEM$STREAM_HAS_DATA('DEV_STAGING.STREAMS.stream_customer_changes');

-- View stream contents
-- SELECT 
--     METADATA$ACTION,
--     METADATA$ISUPDATE,
--     METADATA$ROW_ID,
--     customer_id,
--     first_name,
--     last_name,
--     email,
--     cdc_operation
-- FROM stream_customer_changes
-- LIMIT 10;


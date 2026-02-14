-- ============================================================================
-- Snowflake Streams for Change Data Capture (CDC)
-- Detects changes in source tables for incremental processing
-- ============================================================================

USE DATABASE DEV_STAGING;
USE SCHEMA STREAMS;

-- ============================================================================
-- Stream: POS Data Changes
-- ============================================================================

CREATE OR REPLACE STREAM stream_pos_changes
ON TABLE DEV_RAW.BRONZE.raw_pos
COMMENT = 'Stream to capture changes in raw POS data';

-- ============================================================================
-- Stream: Orders Data Changes
-- ============================================================================

CREATE OR REPLACE STREAM stream_orders_changes
ON TABLE DEV_RAW.BRONZE.raw_orders
COMMENT = 'Stream to capture changes in raw orders data';

-- ============================================================================
-- Stream: Inventory Data Changes
-- ============================================================================

CREATE OR REPLACE STREAM stream_inventory_changes
ON TABLE DEV_RAW.BRONZE.raw_inventory
COMMENT = 'Stream to capture changes in raw inventory data';

-- ============================================================================
-- Stream: Customer Data Changes (Silver Layer)
-- ============================================================================

CREATE OR REPLACE STREAM stream_customer_changes
ON TABLE DEV_STAGING.SILVER.stg_customers
COMMENT = 'Stream to capture changes in staging customer data';

-- ============================================================================
-- Stream: Product Data Changes (Silver Layer)
-- ============================================================================

CREATE OR REPLACE STREAM stream_product_changes
ON TABLE DEV_STAGING.SILVER.stg_products
COMMENT = 'Stream to capture changes in staging product data';

-- ============================================================================
-- Grant Permissions
-- ============================================================================

GRANT SELECT ON STREAM DEV_STAGING.STREAMS.stream_pos_changes TO ROLE DATA_ENGINEER;
GRANT SELECT ON STREAM DEV_STAGING.STREAMS.stream_orders_changes TO ROLE DATA_ENGINEER;
GRANT SELECT ON STREAM DEV_STAGING.STREAMS.stream_inventory_changes TO ROLE DATA_ENGINEER;
GRANT SELECT ON STREAM DEV_STAGING.STREAMS.stream_customer_changes TO ROLE DATA_ENGINEER;
GRANT SELECT ON STREAM DEV_STAGING.STREAMS.stream_product_changes TO ROLE DATA_ENGINEER;


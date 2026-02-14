-- ============================================================================
-- Scenario B: Real-Time Ingestion from Kafka via Snowpipe Streaming
-- Creates PIPE object for Snowpipe Streaming ingestion
-- ============================================================================

USE DATABASE DEV_RAW;
USE SCHEMA BRONZE;

-- ============================================================================
-- Target Table for POS Events
-- ============================================================================

CREATE OR REPLACE TABLE pos_events (
    -- Ingestion metadata (automatically added by Snowpipe Streaming)
    RECORD_METADATA VARIANT,  -- Contains ingestion metadata
    
    -- Event data
    event_id VARCHAR(100) NOT NULL,
    event_timestamp TIMESTAMP_NTZ NOT NULL,
    event_type VARCHAR(50) NOT NULL,  -- 'INSERT', 'UPDATE', 'REFUND'
    
    -- Transaction details
    transaction_id VARCHAR(100) NOT NULL,
    transaction_timestamp TIMESTAMP_NTZ NOT NULL,
    
    -- Store information
    store_id VARCHAR(50) NOT NULL,
    register_id VARCHAR(50),
    
    -- Customer information
    customer_id VARCHAR(100),
    
    -- Product information
    product_id VARCHAR(100) NOT NULL,
    product_sku VARCHAR(100),
    
    -- Transaction amounts
    quantity NUMBER(10,2) NOT NULL,
    unit_price NUMBER(10,2) NOT NULL,
    discount_amount NUMBER(10,2) DEFAULT 0,
    tax_amount NUMBER(10,2) DEFAULT 0,
    total_amount NUMBER(10,2) NOT NULL,
    
    -- Payment information
    payment_method VARCHAR(50),
    payment_status VARCHAR(50),
    
    -- Event source metadata
    kafka_topic VARCHAR(255),
    kafka_partition NUMBER,
    kafka_offset NUMBER,
    
    -- Audit columns
    ingested_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY (transaction_date)  -- Clustering for performance
COMMENT = 'Real-time POS events ingested via Snowpipe Streaming';

-- Add computed column for transaction_date (derived from transaction_timestamp)
ALTER TABLE pos_events ADD COLUMN transaction_date DATE AS (DATE(transaction_timestamp));

-- ============================================================================
-- Create PIPE Object for Snowpipe Streaming
-- ============================================================================

CREATE OR REPLACE PIPE pipe_pos_events_streaming
  AUTO_INGEST = TRUE
  COMMENT = 'Snowpipe Streaming pipe for POS events from Kafka'
AS
INSERT INTO pos_events (
    event_id,
    event_timestamp,
    event_type,
    transaction_id,
    transaction_timestamp,
    store_id,
    register_id,
    customer_id,
    product_id,
    product_sku,
    quantity,
    unit_price,
    discount_amount,
    tax_amount,
    total_amount,
    payment_method,
    payment_status,
    kafka_topic,
    kafka_partition,
    kafka_offset,
    ingested_at
)
SELECT 
    -- Transformations during ingestion
    $1:event_id::VARCHAR(100) AS event_id,
    $1:event_timestamp::TIMESTAMP_NTZ AS event_timestamp,
    $1:event_type::VARCHAR(50) AS event_type,
    $1:transaction_id::VARCHAR(100) AS transaction_id,
    $1:transaction_timestamp::TIMESTAMP_NTZ AS transaction_timestamp,
    TRIM(UPPER($1:store_id::VARCHAR)) AS store_id,
    $1:register_id::VARCHAR(50) AS register_id,
    NULLIF($1:customer_id::VARCHAR, '') AS customer_id,
    TRIM(UPPER($1:product_id::VARCHAR)) AS product_id,
    $1:product_sku::VARCHAR(100) AS product_sku,
    $1:quantity::NUMBER(10,2) AS quantity,
    $1:unit_price::NUMBER(10,2) AS unit_price,
    COALESCE($1:discount_amount::NUMBER(10,2), 0) AS discount_amount,
    COALESCE($1:tax_amount::NUMBER(10,2), 0) AS tax_amount,
    $1:total_amount::NUMBER(10,2) AS total_amount,
    TRIM(UPPER($1:payment_method::VARCHAR)) AS payment_method,
    TRIM(UPPER($1:payment_status::VARCHAR)) AS payment_status,
    $1:kafka_topic::VARCHAR(255) AS kafka_topic,
    $1:kafka_partition::NUMBER AS kafka_partition,
    $1:kafka_offset::NUMBER AS kafka_offset,
    CURRENT_TIMESTAMP() AS ingested_at;

-- ============================================================================
-- Grant Permissions
-- ============================================================================

GRANT OWNERSHIP ON PIPE DEV_RAW.BRONZE.pipe_pos_events_streaming TO ROLE DATA_ENGINEER;

-- ============================================================================
-- Note: For Snowpipe Streaming, you need to use the SDK to write data
-- See Python/Java client code in separate files
-- ============================================================================


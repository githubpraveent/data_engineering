-- ============================================================================
-- Scenario D: Real-Time Aggregated Analytics with Dynamic Tables
-- Creates ingestion table for high-frequency retail events
-- ============================================================================

USE DATABASE DEV_RAW;
USE SCHEMA BRONZE;

-- ============================================================================
-- Retail Events Table
-- Stores high-frequency POS and inventory events
-- ============================================================================

CREATE OR REPLACE TABLE retail_events (
    -- Event metadata
    event_id VARCHAR(100) NOT NULL,
    event_timestamp TIMESTAMP_NTZ NOT NULL,
    event_type VARCHAR(50) NOT NULL,  -- 'SALE', 'REFUND', 'INVENTORY_CHANGE'
    
    -- Store information
    store_id VARCHAR(50) NOT NULL,
    
    -- Product information
    product_id VARCHAR(100) NOT NULL,
    
    -- Transaction details (for SALES/REFUNDS)
    transaction_id VARCHAR(100),
    quantity NUMBER(10,2),
    unit_price NUMBER(10,2),
    total_amount NUMBER(10,2),
    
    -- Inventory details (for INVENTORY_CHANGE)
    inventory_change_type VARCHAR(50),  -- 'STOCK_IN', 'STOCK_OUT', 'ADJUSTMENT'
    inventory_change_quantity NUMBER(10,2),
    
    -- Additional metadata
    source_system VARCHAR(50) DEFAULT 'POS_SYSTEM',
    channel VARCHAR(50),  -- 'IN_STORE', 'ONLINE', 'MOBILE'
    
    -- Audit columns
    ingested_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY (event_timestamp)
COMMENT = 'High-frequency retail events for real-time aggregation';

-- ============================================================================
-- Create Indexes
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_retail_events_timestamp ON retail_events(event_timestamp);
CREATE INDEX IF NOT EXISTS idx_retail_events_store ON retail_events(store_id);
CREATE INDEX IF NOT EXISTS idx_retail_events_type ON retail_events(event_type);


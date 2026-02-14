-- ============================================================================
-- Scenario A: Batch Data Ingestion - Raw Sales Table
-- Creates raw landing table for sales data
-- ============================================================================

USE DATABASE DEV_RAW;
USE SCHEMA BRONZE;

-- ============================================================================
-- Raw Sales Table
-- ============================================================================

CREATE OR REPLACE TABLE raw_sales (
    -- Metadata columns
    file_name VARCHAR(500),
    file_row_number NUMBER,
    load_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    -- Sales data columns
    transaction_id VARCHAR(100) NOT NULL,
    transaction_date DATE NOT NULL,
    transaction_time TIME,
    transaction_timestamp TIMESTAMP_NTZ,
    
    -- Store information
    store_id VARCHAR(50) NOT NULL,
    store_name VARCHAR(255),
    
    -- Customer information
    customer_id VARCHAR(100),
    customer_name VARCHAR(255),
    
    -- Product information
    product_id VARCHAR(100) NOT NULL,
    product_sku VARCHAR(100),
    product_name VARCHAR(255),
    
    -- Transaction details
    quantity NUMBER(10,2) NOT NULL,
    unit_price NUMBER(10,2) NOT NULL,
    discount_amount NUMBER(10,2) DEFAULT 0,
    tax_amount NUMBER(10,2) DEFAULT 0,
    total_amount NUMBER(10,2) NOT NULL,
    
    -- Payment information
    payment_method VARCHAR(50),
    payment_status VARCHAR(50),
    
    -- Additional fields
    sales_channel VARCHAR(50),
    promotion_code VARCHAR(50),
    
    -- Raw data as VARIANT for flexibility
    raw_data VARIANT,
    
    -- Audit columns
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY (transaction_date, store_id)
COMMENT = 'Raw sales data from batch file ingestion';

-- ============================================================================
-- Create Indexes for Performance
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_raw_sales_transaction_date ON raw_sales(transaction_date);
CREATE INDEX IF NOT EXISTS idx_raw_sales_transaction_id ON raw_sales(transaction_id);
CREATE INDEX IF NOT EXISTS idx_raw_sales_store_id ON raw_sales(store_id);


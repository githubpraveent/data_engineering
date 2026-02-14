-- ============================================================================
-- Scenario A: Batch Data Ingestion - Warehouse Sales Table
-- Creates deduplicated, clustered warehouse table for analytics
-- ============================================================================

USE DATABASE DEV_DW;
USE SCHEMA FACTS;

-- ============================================================================
-- Warehouse Sales Table (Deduplicated)
-- ============================================================================

CREATE OR REPLACE TABLE warehouse_sales (
    -- Surrogate key
    sales_key NUMBER(38,0) AUTOINCREMENT START 1 INCREMENT 1,
    
    -- Natural key
    transaction_id VARCHAR(100) NOT NULL,
    product_id VARCHAR(100) NOT NULL,
    
    -- Transaction details
    transaction_date DATE NOT NULL,
    transaction_timestamp TIMESTAMP_NTZ NOT NULL,
    
    -- Store information
    store_id VARCHAR(50) NOT NULL,
    store_name VARCHAR(255),
    
    -- Customer information
    customer_id VARCHAR(100),
    customer_name VARCHAR(255),
    
    -- Product information
    product_sku VARCHAR(100),
    product_name VARCHAR(255),
    
    -- Transaction amounts
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
    
    -- Deduplication tracking
    source_file_name VARCHAR(500),
    load_batch_id VARCHAR(100),
    load_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    -- Audit columns
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY (transaction_date, store_id, product_id)
COMMENT = 'Deduplicated warehouse sales table for analytics';

-- ============================================================================
-- Create Indexes
-- ============================================================================

CREATE UNIQUE INDEX IF NOT EXISTS idx_warehouse_sales_key ON warehouse_sales(sales_key);
CREATE UNIQUE INDEX IF NOT EXISTS idx_warehouse_sales_natural_key ON warehouse_sales(transaction_id, product_id);
CREATE INDEX IF NOT EXISTS idx_warehouse_sales_date ON warehouse_sales(transaction_date);
CREATE INDEX IF NOT EXISTS idx_warehouse_sales_store ON warehouse_sales(store_id);
CREATE INDEX IF NOT EXISTS idx_warehouse_sales_customer ON warehouse_sales(customer_id);


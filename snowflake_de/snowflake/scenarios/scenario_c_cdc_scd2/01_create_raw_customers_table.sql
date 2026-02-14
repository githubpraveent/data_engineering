-- ============================================================================
-- Scenario C: Historical Data + CDC with SCD Type 2 Dimensions
-- Creates raw customers table for batch full extract + incremental CDC
-- ============================================================================

USE DATABASE DEV_RAW;
USE SCHEMA BRONZE;

-- ============================================================================
-- Raw Customers Table
-- ============================================================================

CREATE OR REPLACE TABLE raw_customers (
    -- Metadata columns
    file_name VARCHAR(500),
    file_row_number NUMBER,
    load_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    extract_type VARCHAR(50) DEFAULT 'FULL',  -- 'FULL' or 'INCREMENTAL'
    
    -- Customer data (full extract + CDC)
    customer_id VARCHAR(100) NOT NULL,
    
    -- Customer attributes (Type 2 SCD attributes)
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    full_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    
    -- Address attributes
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    country VARCHAR(50) DEFAULT 'USA',
    
    -- Customer demographics
    date_of_birth DATE,
    registration_date DATE,
    customer_segment VARCHAR(50),
    customer_status VARCHAR(50) DEFAULT 'ACTIVE',
    
    -- CDC metadata
    cdc_operation VARCHAR(10),  -- 'INSERT', 'UPDATE', 'DELETE'
    source_timestamp TIMESTAMP_NTZ,  -- Timestamp from source system
    
    -- Raw data as VARIANT for flexibility
    raw_data VARIANT,
    
    -- Audit columns
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY (customer_id)
COMMENT = 'Raw customer data from batch full extract and incremental CDC';

-- ============================================================================
-- Create Indexes
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_raw_customers_customer_id ON raw_customers(customer_id);
CREATE INDEX IF NOT EXISTS idx_raw_customers_load_timestamp ON raw_customers(load_timestamp);


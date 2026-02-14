-- ============================================================================
-- Scenario C: Historical Data + CDC with SCD Type 2 Dimensions
-- Creates SCD Type 2 customer dimension table
-- ============================================================================

USE DATABASE DEV_DW;
USE SCHEMA DIMENSIONS;

-- ============================================================================
-- Customer Dimension (SCD Type 2)
-- ============================================================================

CREATE OR REPLACE TABLE dim_customers_scd2 (
    -- Surrogate key
    customer_key NUMBER(38,0) AUTOINCREMENT START 1 INCREMENT 1,
    
    -- Business key
    customer_id VARCHAR(100) NOT NULL,
    
    -- Type 2 SCD attributes
    effective_from_date DATE NOT NULL,
    effective_to_date DATE,
    is_current BOOLEAN DEFAULT TRUE,
    
    -- Customer attributes (Type 2 - historical tracking)
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    full_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    
    -- Address attributes (Type 2)
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    country VARCHAR(50) DEFAULT 'USA',
    
    -- Customer demographics (Type 2)
    date_of_birth DATE,
    registration_date DATE,
    customer_segment VARCHAR(50),
    customer_status VARCHAR(50) DEFAULT 'ACTIVE',
    
    -- Audit columns
    source_timestamp TIMESTAMP_NTZ,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    source_system VARCHAR(50) DEFAULT 'CRM_SYSTEM'
)
CLUSTER BY (customer_id, is_current)
COMMENT = 'Customer dimension table with SCD Type 2 support for historical tracking';

-- ============================================================================
-- Create Indexes
-- ============================================================================

CREATE UNIQUE INDEX IF NOT EXISTS idx_dim_customers_scd2_key ON dim_customers_scd2(customer_key);
CREATE INDEX IF NOT EXISTS idx_dim_customers_scd2_customer_id ON dim_customers_scd2(customer_id, is_current);
CREATE INDEX IF NOT EXISTS idx_dim_customers_scd2_effective_dates ON dim_customers_scd2(effective_from_date, effective_to_date);


-- ============================================================================
-- Gold Layer: Dimension Tables
-- Business-ready dimension tables with SCD Type 1 and Type 2 support
-- ============================================================================

USE DATABASE DEV_DW;
USE SCHEMA DIMENSIONS;

-- ============================================================================
-- Dimension: Customer (SCD Type 2 - Historical Tracking)
-- ============================================================================

CREATE OR REPLACE TABLE dim_customer (
    -- Surrogate key
    customer_key NUMBER(38,0) AUTOINCREMENT START 1 INCREMENT 1,
    
    -- Business key
    customer_id VARCHAR(100) NOT NULL,
    
    -- Type 2 SCD attributes
    effective_from_date DATE NOT NULL,
    effective_to_date DATE,
    is_current BOOLEAN DEFAULT TRUE,
    
    -- Customer attributes
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
    
    -- Audit columns
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    source_system VARCHAR(50) DEFAULT 'RETAIL_SYSTEM'
)
CLUSTER BY (customer_id, is_current)
COMMENT = 'Customer dimension table with SCD Type 2 support for historical tracking';

-- ============================================================================
-- Dimension: Product (SCD Type 1 - Overwrite)
-- ============================================================================

CREATE OR REPLACE TABLE dim_product (
    -- Surrogate key
    product_key NUMBER(38,0) AUTOINCREMENT START 1 INCREMENT 1,
    
    -- Business key
    product_id VARCHAR(100) NOT NULL,
    
    -- Product identifiers
    product_sku VARCHAR(100) NOT NULL,
    
    -- Product attributes (Type 1 - overwrite on change)
    product_name VARCHAR(255) NOT NULL,
    product_description VARCHAR(500),
    
    -- Product categorization
    category VARCHAR(100),
    subcategory VARCHAR(100),
    brand VARCHAR(100),
    
    -- Pricing (Type 1 - overwrite on change)
    unit_price NUMBER(10,2),
    cost_price NUMBER(10,2),
    
    -- Physical attributes
    weight NUMBER(10,2),
    dimensions VARCHAR(100),
    
    -- Status
    status VARCHAR(50) DEFAULT 'ACTIVE',
    effective_date DATE,
    
    -- Audit columns
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    source_system VARCHAR(50) DEFAULT 'RETAIL_SYSTEM'
)
CLUSTER BY (product_id)
COMMENT = 'Product dimension table with SCD Type 1 support (overwrite on change)';

-- ============================================================================
-- Dimension: Store (SCD Type 2 - Historical Tracking)
-- ============================================================================

CREATE OR REPLACE TABLE dim_store (
    -- Surrogate key
    store_key NUMBER(38,0) AUTOINCREMENT START 1 INCREMENT 1,
    
    -- Business key
    store_id VARCHAR(50) NOT NULL,
    
    -- Type 2 SCD attributes
    effective_from_date DATE NOT NULL,
    effective_to_date DATE,
    is_current BOOLEAN DEFAULT TRUE,
    
    -- Store attributes
    store_name VARCHAR(255),
    store_type VARCHAR(50),
    store_format VARCHAR(50),
    
    -- Location attributes
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    country VARCHAR(50) DEFAULT 'USA',
    region VARCHAR(50),
    district VARCHAR(50),
    
    -- Store characteristics
    square_footage NUMBER(10,2),
    number_of_registers NUMBER(5,0),
    opening_date DATE,
    closing_date DATE,
    status VARCHAR(50) DEFAULT 'ACTIVE',
    
    -- Audit columns
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    source_system VARCHAR(50) DEFAULT 'RETAIL_SYSTEM'
)
CLUSTER BY (store_id, is_current)
COMMENT = 'Store dimension table with SCD Type 2 support for historical tracking';

-- ============================================================================
-- Dimension: Date (Conformed Dimension)
-- ============================================================================

CREATE OR REPLACE TABLE dim_date (
    date_key NUMBER(38,0) NOT NULL,
    date_value DATE NOT NULL,
    
    -- Date attributes
    day_of_week NUMBER(1,0),  -- 1=Sunday, 7=Saturday
    day_name VARCHAR(10),
    day_of_month NUMBER(2,0),
    day_of_year NUMBER(3,0),
    
    -- Week attributes
    week_of_year NUMBER(2,0),
    week_start_date DATE,
    week_end_date DATE,
    
    -- Month attributes
    month_number NUMBER(2,0),
    month_name VARCHAR(10),
    month_abbreviation VARCHAR(3),
    month_start_date DATE,
    month_end_date DATE,
    
    -- Quarter attributes
    quarter_number NUMBER(1,0),
    quarter_name VARCHAR(10),
    quarter_start_date DATE,
    quarter_end_date DATE,
    
    -- Year attributes
    year_number NUMBER(4,0),
    year_start_date DATE,
    year_end_date DATE,
    
    -- Fiscal attributes (adjust based on your fiscal calendar)
    fiscal_year NUMBER(4,0),
    fiscal_quarter NUMBER(1,0),
    fiscal_month NUMBER(2,0),
    
    -- Flags
    is_weekend BOOLEAN,
    is_holiday BOOLEAN,
    holiday_name VARCHAR(100),
    is_business_day BOOLEAN,
    
    -- Audit columns
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY (date_value)
COMMENT = 'Date dimension table for time-based analysis';

-- ============================================================================
-- Dimension: Time (Conformed Dimension)
-- ============================================================================

CREATE OR REPLACE TABLE dim_time (
    time_key NUMBER(38,0) NOT NULL,
    time_value TIME NOT NULL,
    
    -- Time attributes
    hour_24 NUMBER(2,0),  -- 0-23
    hour_12 NUMBER(2,0),  -- 1-12
    minute NUMBER(2,0),  -- 0-59
    second NUMBER(2,0),  -- 0-59
    
    -- Period attributes
    am_pm VARCHAR(2),
    hour_of_day VARCHAR(20),  -- Morning, Afternoon, Evening, Night
    time_period VARCHAR(20),  -- Early Morning, Morning, Midday, etc.
    
    -- Audit columns
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY (time_value)
COMMENT = 'Time dimension table for time-of-day analysis';

-- ============================================================================
-- Create Indexes for Performance
-- ============================================================================

CREATE UNIQUE INDEX IF NOT EXISTS idx_dim_customer_key ON dim_customer(customer_key);
CREATE INDEX IF NOT EXISTS idx_dim_customer_id ON dim_customer(customer_id, is_current);
CREATE UNIQUE INDEX IF NOT EXISTS idx_dim_product_key ON dim_product(product_key);
CREATE UNIQUE INDEX IF NOT EXISTS idx_dim_product_id ON dim_product(product_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_dim_store_key ON dim_store(store_key);
CREATE INDEX IF NOT EXISTS idx_dim_store_id ON dim_store(store_id, is_current);
CREATE UNIQUE INDEX IF NOT EXISTS idx_dim_date_key ON dim_date(date_key);
CREATE UNIQUE INDEX IF NOT EXISTS idx_dim_date_value ON dim_date(date_value);
CREATE UNIQUE INDEX IF NOT EXISTS idx_dim_time_key ON dim_time(time_key);


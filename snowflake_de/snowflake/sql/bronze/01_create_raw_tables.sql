-- ============================================================================
-- Bronze Layer: Raw Landing Tables
-- Stores raw data exactly as received from source systems
-- ============================================================================

USE DATABASE DEV_RAW;
USE SCHEMA BRONZE;

-- ============================================================================
-- Raw POS Data Table
-- ============================================================================

CREATE OR REPLACE TABLE raw_pos (
    -- Metadata columns
    file_name VARCHAR(500),
    file_row_number NUMBER,
    load_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    -- Raw data columns (adjust based on actual POS system schema)
    transaction_id VARCHAR(100),
    store_id VARCHAR(50),
    register_id VARCHAR(50),
    transaction_date TIMESTAMP_NTZ,
    transaction_time TIME,
    customer_id VARCHAR(100),
    product_id VARCHAR(100),
    product_sku VARCHAR(100),
    quantity NUMBER(10,2),
    unit_price NUMBER(10,2),
    discount_amount NUMBER(10,2),
    tax_amount NUMBER(10,2),
    total_amount NUMBER(10,2),
    payment_method VARCHAR(50),
    payment_status VARCHAR(50),
    
    -- Raw data as VARIANT for flexibility
    raw_data VARIANT,
    
    -- Audit columns
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY (transaction_date, store_id)
COMMENT = 'Raw POS transaction data from source system';

-- ============================================================================
-- Raw Orders Data Table
-- ============================================================================

CREATE OR REPLACE TABLE raw_orders (
    -- Metadata columns
    file_name VARCHAR(500),
    file_row_number NUMBER,
    load_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    -- Raw JSON data stored as VARIANT
    order_data VARIANT,
    
    -- Extracted key fields for partitioning/indexing
    order_id VARCHAR(100) AS (order_data:order_id::VARCHAR),
    order_date DATE AS (order_data:order_date::DATE),
    customer_id VARCHAR(100) AS (order_data:customer_id::VARCHAR),
    
    -- Audit columns
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY (order_date, customer_id)
COMMENT = 'Raw orders data from source system (JSON format)';

-- ============================================================================
-- Raw Inventory Data Table
-- ============================================================================

CREATE OR REPLACE TABLE raw_inventory (
    -- Metadata columns
    file_name VARCHAR(500),
    file_row_number NUMBER,
    load_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    -- Raw data columns
    store_id VARCHAR(50),
    product_id VARCHAR(100),
    product_sku VARCHAR(100),
    inventory_date DATE,
    quantity_on_hand NUMBER(10,2),
    quantity_reserved NUMBER(10,2),
    quantity_available NUMBER(10,2),
    reorder_point NUMBER(10,2),
    reorder_quantity NUMBER(10,2),
    unit_cost NUMBER(10,2),
    location VARCHAR(100),
    
    -- Raw data as VARIANT for flexibility
    raw_data VARIANT,
    
    -- Audit columns
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY (inventory_date, store_id, product_id)
COMMENT = 'Raw inventory data from source system';

-- ============================================================================
-- Raw Customer Data Table
-- ============================================================================

CREATE OR REPLACE TABLE raw_customers (
    -- Metadata columns
    file_name VARCHAR(500),
    file_row_number NUMBER,
    load_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    -- Raw data columns
    customer_id VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(50),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    country VARCHAR(50),
    date_of_birth DATE,
    registration_date DATE,
    customer_segment VARCHAR(50),
    
    -- Raw data as VARIANT for flexibility
    raw_data VARIANT,
    
    -- Audit columns
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY (customer_id)
COMMENT = 'Raw customer data from source system';

-- ============================================================================
-- Raw Product Data Table
-- ============================================================================

CREATE OR REPLACE TABLE raw_products (
    -- Metadata columns
    file_name VARCHAR(500),
    file_row_number NUMBER,
    load_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    -- Raw data columns
    product_id VARCHAR(100),
    product_sku VARCHAR(100),
    product_name VARCHAR(255),
    product_description VARCHAR(500),
    category VARCHAR(100),
    subcategory VARCHAR(100),
    brand VARCHAR(100),
    unit_price NUMBER(10,2),
    cost_price NUMBER(10,2),
    weight NUMBER(10,2),
    dimensions VARCHAR(100),
    status VARCHAR(50),
    effective_date DATE,
    
    -- Raw data as VARIANT for flexibility
    raw_data VARIANT,
    
    -- Audit columns
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY (product_id)
COMMENT = 'Raw product data from source system';

-- ============================================================================
-- Create Indexes for Performance
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_raw_pos_transaction_date ON raw_pos(transaction_date);
CREATE INDEX IF NOT EXISTS idx_raw_pos_store_id ON raw_pos(store_id);
CREATE INDEX IF NOT EXISTS idx_raw_orders_order_date ON raw_orders(order_date);
CREATE INDEX IF NOT EXISTS idx_raw_inventory_date ON raw_inventory(inventory_date);


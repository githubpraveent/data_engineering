-- ============================================================================
-- Silver Layer: Staging Tables
-- Cleaned, standardized, and validated data ready for transformation
-- ============================================================================

USE DATABASE DEV_STAGING;
USE SCHEMA SILVER;

-- ============================================================================
-- Staging POS Data Table
-- ============================================================================

CREATE OR REPLACE TABLE stg_pos (
    -- Primary key
    transaction_id VARCHAR(100) NOT NULL,
    
    -- Store information
    store_id VARCHAR(50) NOT NULL,
    register_id VARCHAR(50),
    
    -- Transaction details
    transaction_date DATE NOT NULL,
    transaction_time TIME,
    transaction_timestamp TIMESTAMP_NTZ,
    
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
    
    -- Data quality flags
    is_valid BOOLEAN DEFAULT TRUE,
    validation_errors VARCHAR(1000),
    
    -- Audit columns
    source_file_name VARCHAR(500),
    source_load_timestamp TIMESTAMP_NTZ,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY (transaction_date, store_id)
COMMENT = 'Staging table for cleaned POS transaction data';

-- ============================================================================
-- Staging Orders Data Table
-- ============================================================================

CREATE OR REPLACE TABLE stg_orders (
    -- Primary key
    order_id VARCHAR(100) NOT NULL,
    
    -- Order details
    order_date DATE NOT NULL,
    order_timestamp TIMESTAMP_NTZ,
    order_status VARCHAR(50),
    order_type VARCHAR(50),
    
    -- Customer information
    customer_id VARCHAR(100) NOT NULL,
    
    -- Store information
    store_id VARCHAR(50),
    
    -- Order amounts
    subtotal_amount NUMBER(10,2),
    discount_amount NUMBER(10,2) DEFAULT 0,
    tax_amount NUMBER(10,2) DEFAULT 0,
    shipping_amount NUMBER(10,2) DEFAULT 0,
    total_amount NUMBER(10,2) NOT NULL,
    
    -- Shipping information
    shipping_address_line1 VARCHAR(255),
    shipping_address_line2 VARCHAR(255),
    shipping_city VARCHAR(100),
    shipping_state VARCHAR(50),
    shipping_zip_code VARCHAR(20),
    shipping_country VARCHAR(50),
    
    -- Payment information
    payment_method VARCHAR(50),
    payment_status VARCHAR(50),
    
    -- Data quality flags
    is_valid BOOLEAN DEFAULT TRUE,
    validation_errors VARCHAR(1000),
    
    -- Audit columns
    source_file_name VARCHAR(500),
    source_load_timestamp TIMESTAMP_NTZ,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY (order_date, customer_id)
COMMENT = 'Staging table for cleaned orders data';

-- ============================================================================
-- Staging Order Items Table
-- ============================================================================

CREATE OR REPLACE TABLE stg_order_items (
    -- Composite primary key
    order_id VARCHAR(100) NOT NULL,
    order_item_id VARCHAR(100) NOT NULL,
    
    -- Product information
    product_id VARCHAR(100) NOT NULL,
    product_sku VARCHAR(100),
    
    -- Item details
    quantity NUMBER(10,2) NOT NULL,
    unit_price NUMBER(10,2) NOT NULL,
    discount_amount NUMBER(10,2) DEFAULT 0,
    total_amount NUMBER(10,2) NOT NULL,
    
    -- Data quality flags
    is_valid BOOLEAN DEFAULT TRUE,
    validation_errors VARCHAR(1000),
    
    -- Audit columns
    source_file_name VARCHAR(500),
    source_load_timestamp TIMESTAMP_NTZ,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY (order_id, product_id)
COMMENT = 'Staging table for cleaned order items data';

-- ============================================================================
-- Staging Inventory Data Table
-- ============================================================================

CREATE OR REPLACE TABLE stg_inventory (
    -- Composite primary key
    store_id VARCHAR(50) NOT NULL,
    product_id VARCHAR(100) NOT NULL,
    inventory_date DATE NOT NULL,
    
    -- Product information
    product_sku VARCHAR(100),
    
    -- Inventory quantities
    quantity_on_hand NUMBER(10,2) NOT NULL,
    quantity_reserved NUMBER(10,2) DEFAULT 0,
    quantity_available NUMBER(10,2) NOT NULL,
    
    -- Reorder information
    reorder_point NUMBER(10,2),
    reorder_quantity NUMBER(10,2),
    
    -- Cost information
    unit_cost NUMBER(10,2),
    total_cost NUMBER(10,2),
    
    -- Location information
    location VARCHAR(100),
    
    -- Data quality flags
    is_valid BOOLEAN DEFAULT TRUE,
    validation_errors VARCHAR(1000),
    
    -- Audit columns
    source_file_name VARCHAR(500),
    source_load_timestamp TIMESTAMP_NTZ,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY (inventory_date, store_id, product_id)
COMMENT = 'Staging table for cleaned inventory data';

-- ============================================================================
-- Staging Customer Data Table
-- ============================================================================

CREATE OR REPLACE TABLE stg_customers (
    -- Primary key
    customer_id VARCHAR(100) NOT NULL,
    
    -- Customer name
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    full_name VARCHAR(255),
    
    -- Contact information
    email VARCHAR(255),
    phone VARCHAR(50),
    
    -- Address information
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    country VARCHAR(50) DEFAULT 'USA',
    
    -- Customer attributes
    date_of_birth DATE,
    registration_date DATE,
    customer_segment VARCHAR(50),
    
    -- Data quality flags
    is_valid BOOLEAN DEFAULT TRUE,
    validation_errors VARCHAR(1000),
    
    -- Audit columns
    source_file_name VARCHAR(500),
    source_load_timestamp TIMESTAMP_NTZ,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY (customer_id)
COMMENT = 'Staging table for cleaned customer data';

-- ============================================================================
-- Staging Product Data Table
-- ============================================================================

CREATE OR REPLACE TABLE stg_products (
    -- Primary key
    product_id VARCHAR(100) NOT NULL,
    
    -- Product identifiers
    product_sku VARCHAR(100) NOT NULL,
    
    -- Product information
    product_name VARCHAR(255) NOT NULL,
    product_description VARCHAR(500),
    
    -- Product categorization
    category VARCHAR(100),
    subcategory VARCHAR(100),
    brand VARCHAR(100),
    
    -- Pricing
    unit_price NUMBER(10,2),
    cost_price NUMBER(10,2),
    
    -- Physical attributes
    weight NUMBER(10,2),
    dimensions VARCHAR(100),
    
    -- Status
    status VARCHAR(50) DEFAULT 'ACTIVE',
    effective_date DATE,
    
    -- Data quality flags
    is_valid BOOLEAN DEFAULT TRUE,
    validation_errors VARCHAR(1000),
    
    -- Audit columns
    source_file_name VARCHAR(500),
    source_load_timestamp TIMESTAMP_NTZ,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY (product_id)
COMMENT = 'Staging table for cleaned product data';

-- ============================================================================
-- Create Indexes for Performance
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_stg_pos_transaction_date ON stg_pos(transaction_date);
CREATE INDEX IF NOT EXISTS idx_stg_pos_store_id ON stg_pos(store_id);
CREATE INDEX IF NOT EXISTS idx_stg_orders_order_date ON stg_orders(order_date);
CREATE INDEX IF NOT EXISTS idx_stg_orders_customer_id ON stg_orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_stg_inventory_date ON stg_inventory(inventory_date);


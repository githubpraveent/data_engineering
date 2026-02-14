-- ============================================================================
-- Gold Layer: Fact Tables
-- Transactional fact tables for sales and orders
-- ============================================================================

USE DATABASE DEV_DW;
USE SCHEMA FACTS;

-- ============================================================================
-- Fact: Sales Transactions
-- ============================================================================

CREATE OR REPLACE TABLE fact_sales (
    -- Surrogate keys (foreign keys to dimensions)
    sales_key NUMBER(38,0) AUTOINCREMENT START 1 INCREMENT 1,
    customer_key NUMBER(38,0),
    product_key NUMBER(38,0) NOT NULL,
    store_key NUMBER(38,0) NOT NULL,
    date_key NUMBER(38,0) NOT NULL,
    time_key NUMBER(38,0),
    
    -- Degenerate dimension (transaction identifier)
    transaction_id VARCHAR(100) NOT NULL,
    
    -- Transaction details
    transaction_timestamp TIMESTAMP_NTZ NOT NULL,
    register_id VARCHAR(50),
    
    -- Measures (additive facts)
    quantity NUMBER(10,2) NOT NULL,
    unit_price NUMBER(10,2) NOT NULL,
    discount_amount NUMBER(10,2) DEFAULT 0,
    tax_amount NUMBER(10,2) DEFAULT 0,
    total_amount NUMBER(10,2) NOT NULL,
    
    -- Payment information
    payment_method VARCHAR(50),
    payment_status VARCHAR(50),
    
    -- Audit columns
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    source_system VARCHAR(50) DEFAULT 'RETAIL_SYSTEM'
)
CLUSTER BY (date_key, store_key, product_key)
COMMENT = 'Fact table for sales transactions';

-- ============================================================================
-- Fact: Orders
-- ============================================================================

CREATE OR REPLACE TABLE fact_orders (
    -- Surrogate keys (foreign keys to dimensions)
    order_key NUMBER(38,0) AUTOINCREMENT START 1 INCREMENT 1,
    customer_key NUMBER(38,0) NOT NULL,
    store_key NUMBER(38,0),
    date_key NUMBER(38,0) NOT NULL,
    
    -- Degenerate dimension (order identifier)
    order_id VARCHAR(100) NOT NULL,
    
    -- Order details
    order_timestamp TIMESTAMP_NTZ NOT NULL,
    order_status VARCHAR(50),
    order_type VARCHAR(50),
    
    -- Measures (additive facts)
    item_count NUMBER(10,0),
    subtotal_amount NUMBER(10,2),
    discount_amount NUMBER(10,2) DEFAULT 0,
    tax_amount NUMBER(10,2) DEFAULT 0,
    shipping_amount NUMBER(10,2) DEFAULT 0,
    total_amount NUMBER(10,2) NOT NULL,
    
    -- Payment information
    payment_method VARCHAR(50),
    payment_status VARCHAR(50),
    
    -- Audit columns
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    source_system VARCHAR(50) DEFAULT 'RETAIL_SYSTEM'
)
CLUSTER BY (date_key, customer_key)
COMMENT = 'Fact table for orders';

-- ============================================================================
-- Fact: Order Items (Line Item Fact)
-- ============================================================================

CREATE OR REPLACE TABLE fact_order_items (
    -- Surrogate keys
    order_item_key NUMBER(38,0) AUTOINCREMENT START 1 INCREMENT 1,
    order_key NUMBER(38,0) NOT NULL,
    product_key NUMBER(38,0) NOT NULL,
    date_key NUMBER(38,0) NOT NULL,
    
    -- Degenerate dimensions
    order_id VARCHAR(100) NOT NULL,
    order_item_id VARCHAR(100) NOT NULL,
    
    -- Measures
    quantity NUMBER(10,2) NOT NULL,
    unit_price NUMBER(10,2) NOT NULL,
    discount_amount NUMBER(10,2) DEFAULT 0,
    total_amount NUMBER(10,2) NOT NULL,
    
    -- Audit columns
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    source_system VARCHAR(50) DEFAULT 'RETAIL_SYSTEM'
)
CLUSTER BY (order_key, product_key)
COMMENT = 'Fact table for order line items';

-- ============================================================================
-- Fact: Inventory Snapshot (Periodic Snapshot Fact)
-- ============================================================================

CREATE OR REPLACE TABLE fact_inventory_snapshot (
    -- Surrogate keys
    inventory_snapshot_key NUMBER(38,0) AUTOINCREMENT START 1 INCREMENT 1,
    store_key NUMBER(38,0) NOT NULL,
    product_key NUMBER(38,0) NOT NULL,
    date_key NUMBER(38,0) NOT NULL,
    
    -- Measures
    quantity_on_hand NUMBER(10,2) NOT NULL,
    quantity_reserved NUMBER(10,2) DEFAULT 0,
    quantity_available NUMBER(10,2) NOT NULL,
    unit_cost NUMBER(10,2),
    total_cost NUMBER(10,2),
    
    -- Reorder information
    reorder_point NUMBER(10,2),
    reorder_quantity NUMBER(10,2),
    days_supply NUMBER(10,2),
    
    -- Location
    location VARCHAR(100),
    
    -- Audit columns
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    source_system VARCHAR(50) DEFAULT 'RETAIL_SYSTEM'
)
CLUSTER BY (date_key, store_key, product_key)
COMMENT = 'Periodic snapshot fact table for inventory levels';

-- ============================================================================
-- Create Indexes for Performance
-- ============================================================================

CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_sales_key ON fact_sales(sales_key);
CREATE INDEX IF NOT EXISTS idx_fact_sales_date ON fact_sales(date_key);
CREATE INDEX IF NOT EXISTS idx_fact_sales_store ON fact_sales(store_key);
CREATE INDEX IF NOT EXISTS idx_fact_sales_product ON fact_sales(product_key);
CREATE INDEX IF NOT EXISTS idx_fact_sales_customer ON fact_sales(customer_key);
CREATE INDEX IF NOT EXISTS idx_fact_sales_transaction_id ON fact_sales(transaction_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_orders_key ON fact_orders(order_key);
CREATE INDEX IF NOT EXISTS idx_fact_orders_date ON fact_orders(date_key);
CREATE INDEX IF NOT EXISTS idx_fact_orders_customer ON fact_orders(customer_key);
CREATE INDEX IF NOT EXISTS idx_fact_orders_order_id ON fact_orders(order_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_order_items_key ON fact_order_items(order_item_key);
CREATE INDEX IF NOT EXISTS idx_fact_order_items_order ON fact_order_items(order_key);
CREATE INDEX IF NOT EXISTS idx_fact_order_items_product ON fact_order_items(product_key);

CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_inventory_snapshot_key ON fact_inventory_snapshot(inventory_snapshot_key);
CREATE INDEX IF NOT EXISTS idx_fact_inventory_snapshot_date ON fact_inventory_snapshot(date_key);
CREATE INDEX IF NOT EXISTS idx_fact_inventory_snapshot_store ON fact_inventory_snapshot(store_key);
CREATE INDEX IF NOT EXISTS idx_fact_inventory_snapshot_product ON fact_inventory_snapshot(product_key);


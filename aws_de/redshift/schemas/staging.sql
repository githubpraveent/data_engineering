-- Redshift Staging Schema
-- Raw tables for data ingested from Kafka and S3

-- Customer Staging Table (from Kafka streaming)
CREATE TABLE IF NOT EXISTS staging.customer_streaming (
    operation VARCHAR(1),
    change_timestamp TIMESTAMP,
    customer_id INTEGER,
    customer_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    kafka_timestamp TIMESTAMP,
    ingestion_timestamp TIMESTAMP,
    partition INTEGER,
    offset BIGINT
)
DISTSTYLE KEY
DISTKEY (customer_id)
SORTKEY (change_timestamp);

-- Order Staging Table (from Kafka streaming)
CREATE TABLE IF NOT EXISTS staging.order_streaming (
    operation VARCHAR(1),
    change_timestamp TIMESTAMP,
    order_id INTEGER,
    customer_id INTEGER,
    order_date TIMESTAMP,
    total_amount DECIMAL(10, 2),
    status VARCHAR(50),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    kafka_timestamp TIMESTAMP,
    ingestion_timestamp TIMESTAMP,
    partition INTEGER,
    offset BIGINT
)
DISTSTYLE KEY
DISTKEY (order_id)
SORTKEY (change_timestamp);

-- Customer Staging Table (from S3 batch load)
CREATE TABLE IF NOT EXISTS staging.customer_batch (
    customer_id INTEGER,
    customer_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    processed_at TIMESTAMP,
    is_valid BOOLEAN
)
DISTSTYLE KEY
DISTKEY (customer_id)
SORTKEY (updated_at);

-- Order Staging Table (from S3 batch load)
CREATE TABLE IF NOT EXISTS staging.order_batch (
    order_id INTEGER,
    customer_id INTEGER,
    order_date TIMESTAMP,
    total_amount DECIMAL(10, 2),
    status VARCHAR(50),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    processed_at TIMESTAMP,
    is_valid BOOLEAN
)
DISTSTYLE KEY
DISTKEY (order_id)
SORTKEY (order_date);

-- Order Item Staging Table
CREATE TABLE IF NOT EXISTS staging.order_item_batch (
    order_item_id INTEGER,
    order_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    unit_price DECIMAL(10, 2),
    total_price DECIMAL(10, 2),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    processed_at TIMESTAMP,
    is_valid BOOLEAN
)
DISTSTYLE KEY
DISTKEY (order_id)
SORTKEY (order_id);

-- Product Staging Table
CREATE TABLE IF NOT EXISTS staging.product_batch (
    product_id INTEGER,
    product_name VARCHAR(255),
    category VARCHAR(100),
    price DECIMAL(10, 2),
    description TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    processed_at TIMESTAMP,
    is_valid BOOLEAN
)
DISTSTYLE KEY
DISTKEY (product_id)
SORTKEY (product_id);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON staging.customer_streaming TO PUBLIC;
GRANT SELECT, INSERT, UPDATE, DELETE ON staging.order_streaming TO PUBLIC;
GRANT SELECT, INSERT, UPDATE, DELETE ON staging.customer_batch TO PUBLIC;
GRANT SELECT, INSERT, UPDATE, DELETE ON staging.order_batch TO PUBLIC;
GRANT SELECT, INSERT, UPDATE, DELETE ON staging.order_item_batch TO PUBLIC;
GRANT SELECT, INSERT, UPDATE, DELETE ON staging.product_batch TO PUBLIC;


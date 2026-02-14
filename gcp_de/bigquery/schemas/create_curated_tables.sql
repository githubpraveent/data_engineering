-- Create curated (gold) tables in BigQuery
-- These tables contain clean, modeled data ready for analytics

-- Customer Dimension (SCD Type 2)
CREATE TABLE IF NOT EXISTS `{project_id}.{curated_dataset}.customer_dimension`
(
    customer_id STRING NOT NULL,
    first_name STRING,
    last_name STRING,
    email STRING,
    address STRING,
    city STRING,
    state STRING,
    zip_code STRING,
    country STRING,
    phone STRING,
    customer_segment STRING,
    registration_date DATE,
    effective_date TIMESTAMP NOT NULL,
    expiration_date TIMESTAMP,
    is_current BOOLEAN NOT NULL,
    load_timestamp TIMESTAMP
)
PARTITION BY DATE(effective_date)
CLUSTER BY customer_id, is_current
OPTIONS(
    description="Customer dimension table with SCD Type 2 support for historical tracking",
    labels=[("environment", "{environment}"), ("purpose", "curated"), ("type", "dimension")]
);

-- Product Dimension (SCD Type 2)
CREATE TABLE IF NOT EXISTS `{project_id}.{curated_dataset}.product_dimension`
(
    product_id STRING NOT NULL,
    product_name STRING,
    category STRING,
    subcategory STRING,
    price FLOAT64,
    cost FLOAT64,
    description STRING,
    brand STRING,
    effective_date TIMESTAMP NOT NULL,
    expiration_date TIMESTAMP,
    is_current BOOLEAN NOT NULL,
    load_timestamp TIMESTAMP
)
PARTITION BY DATE(effective_date)
CLUSTER BY product_id, is_current
OPTIONS(
    description="Product dimension table with SCD Type 2 support for historical tracking",
    labels=[("environment", "{environment}"), ("purpose", "curated"), ("type", "dimension")]
);

-- Store Dimension (SCD Type 1)
CREATE TABLE IF NOT EXISTS `{project_id}.{curated_dataset}.store_dimension`
(
    store_id STRING NOT NULL,
    store_name STRING,
    address STRING,
    city STRING,
    state STRING,
    zip_code STRING,
    country STRING,
    store_manager STRING,
    phone STRING,
    opening_date DATE,
    store_type STRING,
    square_feet INTEGER,
    load_timestamp TIMESTAMP
)
CLUSTER BY store_id
OPTIONS(
    description="Store dimension table with SCD Type 1 (current state only)",
    labels=[("environment", "{environment}"), ("purpose", "curated"), ("type", "dimension")]
);

-- Date Dimension
CREATE TABLE IF NOT EXISTS `{project_id}.{curated_dataset}.date_dimension`
(
    date_id DATE NOT NULL,
    year INTEGER,
    quarter INTEGER,
    month INTEGER,
    month_name STRING,
    week INTEGER,
    day_of_month INTEGER,
    day_of_week INTEGER,
    day_name STRING,
    is_weekend BOOLEAN,
    is_holiday BOOLEAN,
    holiday_name STRING,
    fiscal_year INTEGER,
    fiscal_quarter INTEGER
)
CLUSTER BY date_id
OPTIONS(
    description="Date dimension table for time-based analysis",
    labels=[("environment", "{environment}"), ("purpose", "curated"), ("type", "dimension")]
);

-- Sales Fact Table
CREATE TABLE IF NOT EXISTS `{project_id}.{curated_dataset}.sales_fact`
(
    transaction_id STRING NOT NULL,
    customer_id STRING NOT NULL,
    product_id STRING NOT NULL,
    store_id STRING,
    transaction_timestamp TIMESTAMP NOT NULL,
    quantity INTEGER,
    unit_price FLOAT64,
    total_amount FLOAT64,
    payment_method STRING,
    load_timestamp TIMESTAMP
)
PARTITION BY DATE(transaction_timestamp)
CLUSTER BY customer_id, product_id, store_id
OPTIONS(
    description="Sales fact table - one row per transaction line item",
    labels=[("environment", "{environment}"), ("purpose", "curated"), ("type", "fact")]
);

-- Inventory Fact Table
CREATE TABLE IF NOT EXISTS `{project_id}.{curated_dataset}.inventory_fact`
(
    product_id STRING NOT NULL,
    store_id STRING NOT NULL,
    snapshot_date DATE NOT NULL,
    quantity_on_hand INTEGER,
    quantity_reserved INTEGER,
    quantity_available INTEGER,
    reorder_level INTEGER,
    needs_reorder BOOLEAN,
    load_timestamp TIMESTAMP
)
PARTITION BY snapshot_date
CLUSTER BY product_id, store_id
OPTIONS(
    description="Inventory fact table - daily snapshots of inventory levels",
    labels=[("environment", "{environment}"), ("purpose", "curated"), ("type", "fact")]
);

-- Customer Activity Fact Table
CREATE TABLE IF NOT EXISTS `{project_id}.{curated_dataset}.customer_activity_fact`
(
    activity_id STRING NOT NULL,
    customer_id STRING NOT NULL,
    activity_type STRING,
    activity_timestamp TIMESTAMP NOT NULL,
    product_id STRING,
    store_id STRING,
    activity_value FLOAT64,
    metadata JSON,
    load_timestamp TIMESTAMP
)
PARTITION BY DATE(activity_timestamp)
CLUSTER BY customer_id, activity_type
OPTIONS(
    description="Customer activity fact table - tracks customer events and interactions",
    labels=[("environment", "{environment}"), ("purpose", "curated"), ("type", "fact")]
);


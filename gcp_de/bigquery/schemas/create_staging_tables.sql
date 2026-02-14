-- Create staging tables in BigQuery
-- These tables store raw/lightly transformed data from Dataflow pipelines

-- Staging Transactions Table
CREATE TABLE IF NOT EXISTS `{project_id}.{staging_dataset}.transactions_staging`
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
    load_timestamp TIMESTAMP,
    source_file STRING
)
PARTITION BY DATE(transaction_timestamp)
CLUSTER BY customer_id, product_id
OPTIONS(
    description="Staging table for transaction data from streaming and batch pipelines",
    labels=[("environment", "{environment}"), ("purpose", "staging")]
);

-- Staging Customers Table
CREATE TABLE IF NOT EXISTS `{project_id}.{staging_dataset}.customers_staging`
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
    load_date DATE,
    load_timestamp TIMESTAMP
)
PARTITION BY load_date
CLUSTER BY customer_id
OPTIONS(
    description="Staging table for customer data",
    labels=[("environment", "{environment}"), ("purpose", "staging")]
);

-- Staging Products Table
CREATE TABLE IF NOT EXISTS `{project_id}.{staging_dataset}.products_staging`
(
    product_id STRING NOT NULL,
    product_name STRING,
    category STRING,
    subcategory STRING,
    price FLOAT64,
    cost FLOAT64,
    description STRING,
    brand STRING,
    load_date DATE,
    load_timestamp TIMESTAMP
)
PARTITION BY load_date
CLUSTER BY product_id
OPTIONS(
    description="Staging table for product data",
    labels=[("environment", "{environment}"), ("purpose", "staging")]
);

-- Staging Stores Table
CREATE TABLE IF NOT EXISTS `{project_id}.{staging_dataset}.stores_staging`
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
    load_date DATE,
    load_timestamp TIMESTAMP
)
PARTITION BY load_date
CLUSTER BY store_id
OPTIONS(
    description="Staging table for store data",
    labels=[("environment", "{environment}"), ("purpose", "staging")]
);

-- Staging Inventory Table
CREATE TABLE IF NOT EXISTS `{project_id}.{staging_dataset}.inventory_staging`
(
    product_id STRING NOT NULL,
    store_id STRING NOT NULL,
    quantity_on_hand INTEGER,
    quantity_reserved INTEGER,
    reorder_level INTEGER,
    snapshot_date DATE,
    load_timestamp TIMESTAMP
)
PARTITION BY snapshot_date
CLUSTER BY product_id, store_id
OPTIONS(
    description="Staging table for inventory snapshots",
    labels=[("environment", "{environment}"), ("purpose", "staging")]
);


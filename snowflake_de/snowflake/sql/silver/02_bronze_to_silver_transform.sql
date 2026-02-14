-- ============================================================================
-- Bronze to Silver Transformation
-- Transforms raw data into cleaned, standardized staging tables
-- ============================================================================

USE DATABASE DEV_STAGING;
USE SCHEMA SILVER;

-- ============================================================================
-- Transform POS Data: Bronze → Silver
-- ============================================================================

CREATE OR REPLACE TASK task_bronze_to_silver_pos
  WAREHOUSE = WH_TRANS
  SCHEDULE = 'USING CRON 0 * * * * UTC'  -- Every hour
AS
INSERT INTO DEV_STAGING.SILVER.stg_pos (
    transaction_id,
    store_id,
    register_id,
    transaction_date,
    transaction_time,
    transaction_timestamp,
    customer_id,
    product_id,
    product_sku,
    quantity,
    unit_price,
    discount_amount,
    tax_amount,
    total_amount,
    payment_method,
    payment_status,
    is_valid,
    validation_errors,
    source_file_name,
    source_load_timestamp,
    created_at,
    updated_at
)
SELECT
    -- Primary key
    COALESCE(transaction_id, 'UNKNOWN_' || UUID_STRING()) AS transaction_id,
    
    -- Store information
    TRIM(UPPER(store_id)) AS store_id,
    TRIM(register_id) AS register_id,
    
    -- Transaction details
    DATE(transaction_date) AS transaction_date,
    transaction_time,
    COALESCE(
        TIMESTAMP_NTZ_FROM_PARTS(transaction_date, transaction_time),
        transaction_date
    ) AS transaction_timestamp,
    
    -- Customer information
    NULLIF(TRIM(customer_id), '') AS customer_id,
    
    -- Product information
    TRIM(UPPER(product_id)) AS product_id,
    TRIM(product_sku) AS product_sku,
    
    -- Transaction amounts (with validation)
    COALESCE(quantity, 0) AS quantity,
    COALESCE(unit_price, 0) AS unit_price,
    COALESCE(discount_amount, 0) AS discount_amount,
    COALESCE(tax_amount, 0) AS tax_amount,
    COALESCE(total_amount, 0) AS total_amount,
    
    -- Payment information
    TRIM(UPPER(payment_method)) AS payment_method,
    TRIM(UPPER(payment_status)) AS payment_status,
    
    -- Data quality validation
    CASE
        WHEN transaction_id IS NULL THEN FALSE
        WHEN store_id IS NULL THEN FALSE
        WHEN product_id IS NULL THEN FALSE
        WHEN quantity <= 0 THEN FALSE
        WHEN unit_price < 0 THEN FALSE
        WHEN total_amount < 0 THEN FALSE
        ELSE TRUE
    END AS is_valid,
    
    -- Validation error messages
    CASE
        WHEN transaction_id IS NULL THEN 'Missing transaction_id; '
        ELSE ''
    END ||
    CASE
        WHEN store_id IS NULL THEN 'Missing store_id; '
        ELSE ''
    END ||
    CASE
        WHEN product_id IS NULL THEN 'Missing product_id; '
        ELSE ''
    END ||
    CASE
        WHEN quantity <= 0 THEN 'Invalid quantity; '
        ELSE ''
    END ||
    CASE
        WHEN unit_price < 0 THEN 'Invalid unit_price; '
        ELSE ''
    END ||
    CASE
        WHEN total_amount < 0 THEN 'Invalid total_amount; '
        ELSE ''
    END AS validation_errors,
    
    -- Audit columns
    file_name AS source_file_name,
    load_timestamp AS source_load_timestamp,
    CURRENT_TIMESTAMP() AS created_at,
    CURRENT_TIMESTAMP() AS updated_at
FROM DEV_RAW.BRONZE.raw_pos
WHERE load_timestamp >= (
    SELECT COALESCE(MAX(source_load_timestamp), '1900-01-01'::TIMESTAMP_NTZ)
    FROM DEV_STAGING.SILVER.stg_pos
);

-- ============================================================================
-- Transform Orders Data: Bronze → Silver
-- ============================================================================

CREATE OR REPLACE TASK task_bronze_to_silver_orders
  WAREHOUSE = WH_TRANS
  SCHEDULE = 'USING CRON 0 * * * * UTC'  -- Every hour
AS
INSERT INTO DEV_STAGING.SILVER.stg_orders (
    order_id,
    order_date,
    order_timestamp,
    order_status,
    order_type,
    customer_id,
    store_id,
    subtotal_amount,
    discount_amount,
    tax_amount,
    shipping_amount,
    total_amount,
    shipping_address_line1,
    shipping_address_line2,
    shipping_city,
    shipping_state,
    shipping_zip_code,
    shipping_country,
    payment_method,
    payment_status,
    is_valid,
    validation_errors,
    source_file_name,
    source_load_timestamp,
    created_at,
    updated_at
)
SELECT
    -- Primary key
    order_data:order_id::VARCHAR AS order_id,
    
    -- Order details
    DATE(order_data:order_date::VARCHAR) AS order_date,
    TRY_TO_TIMESTAMP_NTZ(order_data:order_timestamp::VARCHAR) AS order_timestamp,
    TRIM(UPPER(order_data:order_status::VARCHAR)) AS order_status,
    TRIM(UPPER(order_data:order_type::VARCHAR)) AS order_type,
    
    -- Customer information
    order_data:customer_id::VARCHAR AS customer_id,
    
    -- Store information
    order_data:store_id::VARCHAR AS store_id,
    
    -- Order amounts
    order_data:subtotal_amount::NUMBER(10,2) AS subtotal_amount,
    COALESCE(order_data:discount_amount::NUMBER(10,2), 0) AS discount_amount,
    COALESCE(order_data:tax_amount::NUMBER(10,2), 0) AS tax_amount,
    COALESCE(order_data:shipping_amount::NUMBER(10,2), 0) AS shipping_amount,
    order_data:total_amount::NUMBER(10,2) AS total_amount,
    
    -- Shipping information
    order_data:shipping_address:line1::VARCHAR AS shipping_address_line1,
    order_data:shipping_address:line2::VARCHAR AS shipping_address_line2,
    order_data:shipping_address:city::VARCHAR AS shipping_city,
    order_data:shipping_address:state::VARCHAR AS shipping_state,
    order_data:shipping_address:zip_code::VARCHAR AS shipping_zip_code,
    order_data:shipping_address:country::VARCHAR AS shipping_country,
    
    -- Payment information
    order_data:payment_method::VARCHAR AS payment_method,
    order_data:payment_status::VARCHAR AS payment_status,
    
    -- Data quality validation
    CASE
        WHEN order_data:order_id::VARCHAR IS NULL THEN FALSE
        WHEN order_data:customer_id::VARCHAR IS NULL THEN FALSE
        WHEN order_data:total_amount::NUMBER(10,2) IS NULL THEN FALSE
        WHEN order_data:total_amount::NUMBER(10,2) < 0 THEN FALSE
        ELSE TRUE
    END AS is_valid,
    
    -- Validation error messages
    CASE
        WHEN order_data:order_id::VARCHAR IS NULL THEN 'Missing order_id; '
        ELSE ''
    END ||
    CASE
        WHEN order_data:customer_id::VARCHAR IS NULL THEN 'Missing customer_id; '
        ELSE ''
    END ||
    CASE
        WHEN order_data:total_amount::NUMBER(10,2) IS NULL THEN 'Missing total_amount; '
        ELSE ''
    END ||
    CASE
        WHEN order_data:total_amount::NUMBER(10,2) < 0 THEN 'Invalid total_amount; '
        ELSE ''
    END AS validation_errors,
    
    -- Audit columns
    file_name AS source_file_name,
    load_timestamp AS source_load_timestamp,
    CURRENT_TIMESTAMP() AS created_at,
    CURRENT_TIMESTAMP() AS updated_at
FROM DEV_RAW.BRONZE.raw_orders
WHERE load_timestamp >= (
    SELECT COALESCE(MAX(source_load_timestamp), '1900-01-01'::TIMESTAMP_NTZ)
    FROM DEV_STAGING.SILVER.stg_orders
);

-- ============================================================================
-- Transform Inventory Data: Bronze → Silver
-- ============================================================================

CREATE OR REPLACE TASK task_bronze_to_silver_inventory
  WAREHOUSE = WH_TRANS
  SCHEDULE = 'USING CRON 0 * * * * UTC'  -- Every hour
AS
INSERT INTO DEV_STAGING.SILVER.stg_inventory (
    store_id,
    product_id,
    inventory_date,
    product_sku,
    quantity_on_hand,
    quantity_reserved,
    quantity_available,
    reorder_point,
    reorder_quantity,
    unit_cost,
    total_cost,
    location,
    is_valid,
    validation_errors,
    source_file_name,
    source_load_timestamp,
    created_at,
    updated_at
)
SELECT
    -- Composite primary key
    TRIM(UPPER(store_id)) AS store_id,
    TRIM(UPPER(product_id)) AS product_id,
    DATE(inventory_date) AS inventory_date,
    
    -- Product information
    TRIM(product_sku) AS product_sku,
    
    -- Inventory quantities
    COALESCE(quantity_on_hand, 0) AS quantity_on_hand,
    COALESCE(quantity_reserved, 0) AS quantity_reserved,
    COALESCE(quantity_available, quantity_on_hand - COALESCE(quantity_reserved, 0)) AS quantity_available,
    
    -- Reorder information
    reorder_point,
    reorder_quantity,
    
    -- Cost information
    unit_cost,
    unit_cost * quantity_on_hand AS total_cost,
    
    -- Location information
    TRIM(location) AS location,
    
    -- Data quality validation
    CASE
        WHEN store_id IS NULL THEN FALSE
        WHEN product_id IS NULL THEN FALSE
        WHEN inventory_date IS NULL THEN FALSE
        WHEN quantity_on_hand IS NULL THEN FALSE
        WHEN quantity_on_hand < 0 THEN FALSE
        ELSE TRUE
    END AS is_valid,
    
    -- Validation error messages
    CASE
        WHEN store_id IS NULL THEN 'Missing store_id; '
        ELSE ''
    END ||
    CASE
        WHEN product_id IS NULL THEN 'Missing product_id; '
        ELSE ''
    END ||
    CASE
        WHEN inventory_date IS NULL THEN 'Missing inventory_date; '
        ELSE ''
    END ||
    CASE
        WHEN quantity_on_hand IS NULL THEN 'Missing quantity_on_hand; '
        ELSE ''
    END ||
    CASE
        WHEN quantity_on_hand < 0 THEN 'Invalid quantity_on_hand; '
        ELSE ''
    END AS validation_errors,
    
    -- Audit columns
    file_name AS source_file_name,
    load_timestamp AS source_load_timestamp,
    CURRENT_TIMESTAMP() AS created_at,
    CURRENT_TIMESTAMP() AS updated_at
FROM DEV_RAW.BRONZE.raw_inventory
WHERE load_timestamp >= (
    SELECT COALESCE(MAX(source_load_timestamp), '1900-01-01'::TIMESTAMP_NTZ)
    FROM DEV_STAGING.SILVER.stg_inventory
);

-- ============================================================================
-- Resume tasks (tasks are created in suspended state by default)
-- ============================================================================

ALTER TASK task_bronze_to_silver_pos RESUME;
ALTER TASK task_bronze_to_silver_orders RESUME;
ALTER TASK task_bronze_to_silver_inventory RESUME;


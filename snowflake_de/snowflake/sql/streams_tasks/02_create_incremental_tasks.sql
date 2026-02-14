-- ============================================================================
-- Snowflake Tasks for Incremental Processing
-- Processes changes detected by streams
-- ============================================================================

USE DATABASE DEV_STAGING;
USE SCHEMA TASKS;

-- ============================================================================
-- Task: Process POS Changes (Incremental)
-- ============================================================================

CREATE OR REPLACE TASK task_process_pos_changes
  WAREHOUSE = WH_TRANS
  SCHEDULE = 'USING CRON */15 * * * * UTC'  -- Every 15 minutes
WHEN
  SYSTEM$STREAM_HAS_DATA('DEV_STAGING.STREAMS.stream_pos_changes')
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
    COALESCE(transaction_id, 'UNKNOWN_' || UUID_STRING()) AS transaction_id,
    TRIM(UPPER(store_id)) AS store_id,
    TRIM(register_id) AS register_id,
    DATE(transaction_date) AS transaction_date,
    transaction_time,
    COALESCE(
        TIMESTAMP_NTZ_FROM_PARTS(transaction_date, transaction_time),
        transaction_date
    ) AS transaction_timestamp,
    NULLIF(TRIM(customer_id), '') AS customer_id,
    TRIM(UPPER(product_id)) AS product_id,
    TRIM(product_sku) AS product_sku,
    COALESCE(quantity, 0) AS quantity,
    COALESCE(unit_price, 0) AS unit_price,
    COALESCE(discount_amount, 0) AS discount_amount,
    COALESCE(tax_amount, 0) AS tax_amount,
    COALESCE(total_amount, 0) AS total_amount,
    TRIM(UPPER(payment_method)) AS payment_method,
    TRIM(UPPER(payment_status)) AS payment_status,
    CASE
        WHEN transaction_id IS NULL THEN FALSE
        WHEN store_id IS NULL THEN FALSE
        WHEN product_id IS NULL THEN FALSE
        WHEN quantity <= 0 THEN FALSE
        WHEN unit_price < 0 THEN FALSE
        WHEN total_amount < 0 THEN FALSE
        ELSE TRUE
    END AS is_valid,
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
    file_name AS source_file_name,
    load_timestamp AS source_load_timestamp,
    CURRENT_TIMESTAMP() AS created_at,
    CURRENT_TIMESTAMP() AS updated_at
FROM DEV_STAGING.STREAMS.stream_pos_changes
WHERE METADATA$ACTION = 'INSERT';

-- ============================================================================
-- Task: Process Customer Changes (Incremental SCD Type 2)
-- ============================================================================

CREATE OR REPLACE TASK task_process_customer_changes
  WAREHOUSE = WH_TRANS
  SCHEDULE = 'USING CRON 0 * * * * UTC'  -- Every hour
WHEN
  SYSTEM$STREAM_HAS_DATA('DEV_STAGING.STREAMS.stream_customer_changes')
AS
CALL DEV_DW.DIMENSIONS.sp_load_dim_customer_scd_type2();

-- ============================================================================
-- Task: Process Product Changes (Incremental SCD Type 1)
-- ============================================================================

CREATE OR REPLACE TASK task_process_product_changes
  WAREHOUSE = WH_TRANS
  SCHEDULE = 'USING CRON 0 * * * * UTC'  -- Every hour
WHEN
  SYSTEM$STREAM_HAS_DATA('DEV_STAGING.STREAMS.stream_product_changes')
AS
CALL DEV_DW.DIMENSIONS.sp_load_dim_product_scd_type1();

-- ============================================================================
-- Task: Load Fact Sales (Incremental)
-- ============================================================================

CREATE OR REPLACE TASK task_load_fact_sales
  WAREHOUSE = WH_TRANS
  SCHEDULE = 'USING CRON 0 * * * * UTC'  -- Every hour
  AFTER task_process_pos_changes
AS
CALL DEV_DW.FACTS.sp_load_fact_sales();

-- ============================================================================
-- Resume Tasks (tasks are created in suspended state by default)
-- ============================================================================

ALTER TASK task_process_pos_changes RESUME;
ALTER TASK task_process_customer_changes RESUME;
ALTER TASK task_process_product_changes RESUME;
ALTER TASK task_load_fact_sales RESUME;

-- ============================================================================
-- Grant Permissions
-- ============================================================================

GRANT OPERATE ON TASK DEV_STAGING.TASKS.task_process_pos_changes TO ROLE DATA_ENGINEER;
GRANT OPERATE ON TASK DEV_STAGING.TASKS.task_process_customer_changes TO ROLE DATA_ENGINEER;
GRANT OPERATE ON TASK DEV_STAGING.TASKS.task_process_product_changes TO ROLE DATA_ENGINEER;
GRANT OPERATE ON TASK DEV_STAGING.TASKS.task_load_fact_sales TO ROLE DATA_ENGINEER;


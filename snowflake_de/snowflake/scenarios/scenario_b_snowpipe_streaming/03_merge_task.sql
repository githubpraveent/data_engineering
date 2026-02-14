-- ============================================================================
-- Scenario B: Real-Time Ingestion - Task to MERGE from Stream
-- Periodically processes stream changes into dimension/fact tables
-- ============================================================================

USE DATABASE DEV_STAGING;
USE SCHEMA TASKS;

-- ============================================================================
-- Task: Merge POS Events from Stream to Fact Table
-- ============================================================================

CREATE OR REPLACE TASK task_merge_pos_events_to_fact
  WAREHOUSE = WH_TRANS
  SCHEDULE = 'USING CRON */5 * * * * UTC'  -- Every 5 minutes
WHEN
  SYSTEM$STREAM_HAS_DATA('DEV_STAGING.STREAMS.stream_pos_events_changes')
AS
MERGE INTO DEV_DW.FACTS.fact_sales fs
USING (
    SELECT DISTINCT
        -- Dimension lookups
        dc.customer_key,
        dp.product_key,
        ds.store_key,
        dd.date_key,
        
        -- Transaction details
        spe.transaction_id,
        spe.transaction_timestamp,
        spe.register_id,
        
        -- Measures
        spe.quantity,
        spe.unit_price,
        spe.discount_amount,
        spe.tax_amount,
        spe.total_amount,
        
        -- Payment information
        spe.payment_method,
        spe.payment_status
    FROM DEV_STAGING.STREAMS.stream_pos_events_changes spe
    LEFT JOIN DEV_DW.DIMENSIONS.dim_customer dc
        ON spe.customer_id = dc.customer_id
        AND dc.is_current = TRUE
    INNER JOIN DEV_DW.DIMENSIONS.dim_product dp
        ON spe.product_id = dp.product_id
    INNER JOIN DEV_DW.DIMENSIONS.dim_store ds
        ON spe.store_id = ds.store_id
        AND ds.is_current = TRUE
    INNER JOIN DEV_DW.DIMENSIONS.dim_date dd
        ON DATE(spe.transaction_timestamp) = dd.date_value
    WHERE spe.METADATA$ACTION = 'INSERT'
      AND spe.event_type = 'INSERT'  -- Only process inserts, handle updates/refunds separately
) stream_data
ON fs.transaction_id = stream_data.transaction_id
   AND fs.product_key = stream_data.product_key
WHEN NOT MATCHED THEN
    INSERT (
        customer_key,
        product_key,
        store_key,
        date_key,
        time_key,
        transaction_id,
        transaction_timestamp,
        register_id,
        quantity,
        unit_price,
        discount_amount,
        tax_amount,
        total_amount,
        payment_method,
        payment_status,
        created_at,
        updated_at,
        source_system
    )
    VALUES (
        stream_data.customer_key,
        stream_data.product_key,
        stream_data.store_key,
        stream_data.date_key,
        NULL,  -- time_key would require time dimension lookup
        stream_data.transaction_id,
        stream_data.transaction_timestamp,
        stream_data.register_id,
        stream_data.quantity,
        stream_data.unit_price,
        stream_data.discount_amount,
        stream_data.tax_amount,
        stream_data.total_amount,
        stream_data.payment_method,
        stream_data.payment_status,
        CURRENT_TIMESTAMP(),
        CURRENT_TIMESTAMP(),
        'KAFKA_STREAMING'
    );

-- ============================================================================
-- Resume Task
-- ============================================================================

ALTER TASK task_merge_pos_events_to_fact RESUME;

-- ============================================================================
-- Grant Permissions
-- ============================================================================

GRANT OPERATE ON TASK DEV_STAGING.TASKS.task_merge_pos_events_to_fact TO ROLE DATA_ENGINEER;

-- ============================================================================
-- Task: Handle Updates and Refunds (separate task)
-- ============================================================================

CREATE OR REPLACE TASK task_handle_pos_updates_refunds
  WAREHOUSE = WH_TRANS
  SCHEDULE = 'USING CRON */5 * * * * UTC'  -- Every 5 minutes
WHEN
  SYSTEM$STREAM_HAS_DATA('DEV_STAGING.STREAMS.stream_pos_events_changes')
AS
-- Handle UPDATE events (adjust quantities, amounts)
UPDATE DEV_DW.FACTS.fact_sales fs
SET
    quantity = stream_data.quantity,
    total_amount = stream_data.total_amount,
    updated_at = CURRENT_TIMESTAMP()
FROM (
    SELECT
        spe.transaction_id,
        dp.product_key,
        spe.quantity,
        spe.total_amount
    FROM DEV_STAGING.STREAMS.stream_pos_events_changes spe
    INNER JOIN DEV_DW.DIMENSIONS.dim_product dp
        ON spe.product_id = dp.product_id
    WHERE spe.METADATA$ACTION = 'INSERT'
      AND spe.event_type = 'UPDATE'
) stream_data
WHERE fs.transaction_id = stream_data.transaction_id
  AND fs.product_key = stream_data.product_key;

-- Handle REFUND events (mark as refunded or create negative records)
-- This is a simplified example - actual implementation may vary
INSERT INTO DEV_DW.FACTS.fact_sales (
    customer_key,
    product_key,
    store_key,
    date_key,
    transaction_id,
    transaction_timestamp,
    quantity,
    unit_price,
    discount_amount,
    tax_amount,
    total_amount,
    payment_method,
    payment_status,
    created_at,
    updated_at,
    source_system
)
SELECT
    dc.customer_key,
    dp.product_key,
    ds.store_key,
    dd.date_key,
    spe.transaction_id || '_REFUND' AS transaction_id,
    spe.transaction_timestamp,
    -spe.quantity AS quantity,  -- Negative quantity for refund
    spe.unit_price,
    -spe.discount_amount AS discount_amount,
    -spe.tax_amount AS tax_amount,
    -spe.total_amount AS total_amount,
    spe.payment_method,
    'REFUNDED' AS payment_status,
    CURRENT_TIMESTAMP(),
    CURRENT_TIMESTAMP(),
    'KAFKA_STREAMING'
FROM DEV_STAGING.STREAMS.stream_pos_events_changes spe
LEFT JOIN DEV_DW.DIMENSIONS.dim_customer dc
    ON spe.customer_id = dc.customer_id
    AND dc.is_current = TRUE
INNER JOIN DEV_DW.DIMENSIONS.dim_product dp
    ON spe.product_id = dp.product_id
INNER JOIN DEV_DW.DIMENSIONS.dim_store ds
    ON spe.store_id = ds.store_id
    AND ds.is_current = TRUE
INNER JOIN DEV_DW.DIMENSIONS.dim_date dd
    ON DATE(spe.transaction_timestamp) = dd.date_value
WHERE spe.METADATA$ACTION = 'INSERT'
  AND spe.event_type = 'REFUND';

ALTER TASK task_handle_pos_updates_refunds RESUME;


-- Load Sales Fact Table
-- Incrementally loads sales fact table from staging transactions

INSERT INTO `{project_id}.{curated_dataset}.sales_fact`
(
    transaction_id,
    customer_id,
    product_id,
    store_id,
    transaction_timestamp,
    quantity,
    unit_price,
    total_amount,
    payment_method,
    load_timestamp
)
SELECT 
    ts.transaction_id,
    ts.customer_id,
    ts.product_id,
    ts.store_id,
    ts.transaction_timestamp,
    ts.quantity,
    ts.unit_price,
    ts.total_amount,
    ts.payment_method,
    CURRENT_TIMESTAMP() AS load_timestamp
FROM `{project_id}.{staging_dataset}.transactions_staging` ts
WHERE DATE(ts.transaction_timestamp) = DATE('{load_date}')
AND ts.transaction_id NOT IN (
    -- Avoid duplicates
    SELECT transaction_id
    FROM `{project_id}.{curated_dataset}.sales_fact`
    WHERE DATE(transaction_timestamp) = DATE('{load_date}')
);


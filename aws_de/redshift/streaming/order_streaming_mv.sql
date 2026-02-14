-- Materialized View for Streaming Order Data from MSK
-- Refreshes automatically to consume from Kafka

CREATE MATERIALIZED VIEW IF NOT EXISTS staging.mv_order_streaming
AUTO REFRESH YES
AS
SELECT
    operation,
    change_timestamp,
    order_id,
    customer_id,
    order_date,
    total_amount,
    status,
    created_at,
    updated_at,
    kafka_timestamp,
    ingestion_timestamp
FROM staging.order_streaming
WHERE operation IN ('c', 'u')  -- Only inserts and updates
ORDER BY change_timestamp DESC;

-- Grant permissions
GRANT SELECT ON staging.mv_order_streaming TO PUBLIC;

-- Note: This MV will be configured to consume from MSK topic retail.order.cdc
-- The AUTO REFRESH YES enables automatic refresh every minute


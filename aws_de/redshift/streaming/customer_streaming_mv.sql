-- Materialized View for Streaming Customer Data from MSK
-- Refreshes automatically to consume from Kafka

CREATE MATERIALIZED VIEW IF NOT EXISTS staging.mv_customer_streaming
AUTO REFRESH YES
AS
SELECT
    operation,
    change_timestamp,
    customer_id,
    customer_name,
    email,
    phone,
    address,
    city,
    state,
    zip_code,
    created_at,
    updated_at,
    kafka_timestamp,
    ingestion_timestamp
FROM staging.customer_streaming
WHERE operation IN ('c', 'u')  -- Only inserts and updates
ORDER BY change_timestamp DESC;

-- Grant permissions
GRANT SELECT ON staging.mv_customer_streaming TO PUBLIC;

-- Note: This MV will be configured to consume from MSK topic retail.customer.cdc
-- The AUTO REFRESH YES enables automatic refresh every minute


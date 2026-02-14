-- SCD Type 2: Customer Dimension Update
-- This script handles slowly changing dimensions Type 2 for customer data
-- Expires old records and inserts new records for changed customers

-- Step 1: Expire old records (set is_current = FALSE and expiration_date)
UPDATE `{project_id}.{curated_dataset}.customer_dimension`
SET 
    is_current = FALSE,
    expiration_date = CURRENT_TIMESTAMP()
WHERE is_current = TRUE
AND customer_id IN (
    SELECT DISTINCT customer_id
    FROM `{project_id}.{staging_dataset}.customers_staging`
    WHERE load_date = DATE('{load_date}')
)
AND customer_id NOT IN (
    -- Keep current if no changes detected
    SELECT customer_id
    FROM `{project_id}.{staging_dataset}.customers_staging` cs
    INNER JOIN `{project_id}.{curated_dataset}.customer_dimension` cd
    ON cs.customer_id = cd.customer_id
    WHERE cd.is_current = TRUE
    AND cs.load_date = DATE('{load_date}')
    AND COALESCE(cs.first_name, '') = COALESCE(cd.first_name, '')
    AND COALESCE(cs.last_name, '') = COALESCE(cd.last_name, '')
    AND COALESCE(cs.email, '') = COALESCE(cd.email, '')
    AND COALESCE(cs.address, '') = COALESCE(cd.address, '')
    AND COALESCE(cs.phone, '') = COALESCE(cd.phone, '')
    AND COALESCE(cs.customer_segment, '') = COALESCE(cd.customer_segment, '')
);

-- Step 2: Insert new records for changed or new customers
INSERT INTO `{project_id}.{curated_dataset}.customer_dimension`
(
    customer_id,
    first_name,
    last_name,
    email,
    address,
    city,
    state,
    zip_code,
    country,
    phone,
    customer_segment,
    registration_date,
    effective_date,
    expiration_date,
    is_current,
    load_timestamp
)
SELECT 
    cs.customer_id,
    cs.first_name,
    cs.last_name,
    cs.email,
    cs.address,
    cs.city,
    cs.state,
    cs.zip_code,
    cs.country,
    cs.phone,
    cs.customer_segment,
    cs.registration_date,
    CURRENT_TIMESTAMP() AS effective_date,
    CAST(NULL AS TIMESTAMP) AS expiration_date,
    TRUE AS is_current,
    CURRENT_TIMESTAMP() AS load_timestamp
FROM `{project_id}.{staging_dataset}.customers_staging` cs
LEFT JOIN `{project_id}.{curated_dataset}.customer_dimension` cd
ON cs.customer_id = cd.customer_id
AND cd.is_current = TRUE
WHERE cs.load_date = DATE('{load_date}')
AND (
    -- New customer
    cd.customer_id IS NULL
    OR (
        -- Changed customer (SCD Type 2)
        COALESCE(cs.first_name, '') != COALESCE(cd.first_name, '')
        OR COALESCE(cs.last_name, '') != COALESCE(cd.last_name, '')
        OR COALESCE(cs.email, '') != COALESCE(cd.email, '')
        OR COALESCE(cs.address, '') != COALESCE(cd.address, '')
        OR COALESCE(cs.phone, '') != COALESCE(cd.phone, '')
        OR COALESCE(cs.customer_segment, '') != COALESCE(cd.customer_segment, '')
    )
);


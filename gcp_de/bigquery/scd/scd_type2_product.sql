-- SCD Type 2: Product Dimension Update
-- Handles slowly changing dimensions Type 2 for product data

-- Step 1: Expire old records
UPDATE `{project_id}.{curated_dataset}.product_dimension`
SET 
    is_current = FALSE,
    expiration_date = CURRENT_TIMESTAMP()
WHERE is_current = TRUE
AND product_id IN (
    SELECT DISTINCT product_id
    FROM `{project_id}.{staging_dataset}.products_staging`
    WHERE load_date = DATE('{load_date}')
)
AND product_id NOT IN (
    -- Keep current if no changes
    SELECT product_id
    FROM `{project_id}.{staging_dataset}.products_staging` ps
    INNER JOIN `{project_id}.{curated_dataset}.product_dimension` pd
    ON ps.product_id = pd.product_id
    WHERE pd.is_current = TRUE
    AND ps.load_date = DATE('{load_date}')
    AND COALESCE(ps.product_name, '') = COALESCE(pd.product_name, '')
    AND COALESCE(ps.category, '') = COALESCE(pd.category, '')
    AND COALESCE(ps.price, 0) = COALESCE(pd.price, 0)
    AND COALESCE(ps.description, '') = COALESCE(pd.description, '')
);

-- Step 2: Insert new records for changed or new products
INSERT INTO `{project_id}.{curated_dataset}.product_dimension`
(
    product_id,
    product_name,
    category,
    subcategory,
    price,
    cost,
    description,
    brand,
    effective_date,
    expiration_date,
    is_current,
    load_timestamp
)
SELECT 
    ps.product_id,
    ps.product_name,
    ps.category,
    ps.subcategory,
    ps.price,
    ps.cost,
    ps.description,
    ps.brand,
    CURRENT_TIMESTAMP() AS effective_date,
    CAST(NULL AS TIMESTAMP) AS expiration_date,
    TRUE AS is_current,
    CURRENT_TIMESTAMP() AS load_timestamp
FROM `{project_id}.{staging_dataset}.products_staging` ps
LEFT JOIN `{project_id}.{curated_dataset}.product_dimension` pd
ON ps.product_id = pd.product_id
AND pd.is_current = TRUE
WHERE ps.load_date = DATE('{load_date}')
AND (
    -- New product
    pd.product_id IS NULL
    OR (
        -- Changed product (SCD Type 2)
        COALESCE(ps.product_name, '') != COALESCE(pd.product_name, '')
        OR COALESCE(ps.category, '') != COALESCE(pd.category, '')
        OR COALESCE(ps.price, 0) != COALESCE(pd.price, 0)
        OR COALESCE(ps.description, '') != COALESCE(pd.description, '')
    )
);


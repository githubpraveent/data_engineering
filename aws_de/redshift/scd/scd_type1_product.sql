-- SCD Type 1: Product Dimension (Overwrite)
-- No history maintained, updates overwrite existing records

CREATE OR REPLACE PROCEDURE analytics.sp_scd_type1_product()
AS $$
BEGIN
    -- Update existing products
    UPDATE analytics.dim_product
    SET
        product_name = s.product_name,
        category = s.category,
        price = s.price,
        description = s.description,
        updated_at = GETDATE()
    FROM staging.product_batch s
    WHERE analytics.dim_product.product_id = s.product_id
        AND s.is_valid = TRUE
        AND (
            analytics.dim_product.product_name != s.product_name
            OR analytics.dim_product.category != s.category
            OR analytics.dim_product.price != s.price
            OR COALESCE(analytics.dim_product.description, '') != COALESCE(s.description, '')
        );

    -- Insert new products
    INSERT INTO analytics.dim_product (
        product_id,
        product_name,
        category,
        price,
        description,
        created_at,
        updated_at
    )
    SELECT
        s.product_id,
        s.product_name,
        s.category,
        s.price,
        s.description,
        s.created_at,
        GETDATE()
    FROM staging.product_batch s
    WHERE s.is_valid = TRUE
        AND NOT EXISTS (
            SELECT 1
            FROM analytics.dim_product d
            WHERE d.product_id = s.product_id
        );

    -- Log results
    RAISE NOTICE 'SCD Type 1 Product: Updated % records, Inserted % records',
        (SELECT COUNT(*) FROM staging.product_batch WHERE is_valid = TRUE AND product_id IN (SELECT product_id FROM analytics.dim_product)),
        (SELECT COUNT(*) FROM staging.product_batch WHERE is_valid = TRUE AND product_id NOT IN (SELECT product_id FROM analytics.dim_product));
END;
$$ LANGUAGE plpgsql;

-- Grant execute permission
GRANT EXECUTE ON PROCEDURE analytics.sp_scd_type1_product() TO PUBLIC;


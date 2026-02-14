-- ============================================================================
-- SCD Type 1 Load: Product Dimension
-- Overwrites existing records when changes are detected
-- ============================================================================

USE DATABASE DEV_DW;
USE SCHEMA DIMENSIONS;

-- ============================================================================
-- Stored Procedure: Load Product Dimension (SCD Type 1)
-- ============================================================================

CREATE OR REPLACE PROCEDURE sp_load_dim_product_scd_type1()
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
BEGIN
    -- Step 1: Update existing products (overwrite)
    MERGE INTO dim_product dp
    USING (
        SELECT DISTINCT
            product_id,
            product_sku,
            product_name,
            product_description,
            category,
            subcategory,
            brand,
            unit_price,
            cost_price,
            weight,
            dimensions,
            status,
            effective_date
        FROM DEV_STAGING.SILVER.stg_products
        WHERE is_valid = TRUE
    ) sp
    ON dp.product_id = sp.product_id
    WHEN MATCHED THEN
        UPDATE SET
            product_sku = sp.product_sku,
            product_name = sp.product_name,
            product_description = sp.product_description,
            category = sp.category,
            subcategory = sp.subcategory,
            brand = sp.brand,
            unit_price = sp.unit_price,
            cost_price = sp.cost_price,
            weight = sp.weight,
            dimensions = sp.dimensions,
            status = sp.status,
            effective_date = sp.effective_date,
            updated_at = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN
        INSERT (
            product_id,
            product_sku,
            product_name,
            product_description,
            category,
            subcategory,
            brand,
            unit_price,
            cost_price,
            weight,
            dimensions,
            status,
            effective_date,
            created_at,
            updated_at,
            source_system
        )
        VALUES (
            sp.product_id,
            sp.product_sku,
            sp.product_name,
            sp.product_description,
            sp.category,
            sp.subcategory,
            sp.brand,
            sp.unit_price,
            sp.cost_price,
            sp.weight,
            sp.dimensions,
            sp.status,
            sp.effective_date,
            CURRENT_TIMESTAMP(),
            CURRENT_TIMESTAMP(),
            'RETAIL_SYSTEM'
        );
    
    RETURN 'SUCCESS: Product dimension (SCD Type 1) loaded successfully';
END;
$$;

-- ============================================================================
-- Grant Execute Permission
-- ============================================================================

GRANT USAGE ON PROCEDURE sp_load_dim_product_scd_type1() TO ROLE DATA_ENGINEER;


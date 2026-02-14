-- ============================================================================
-- Load Fact Sales Table
-- Transforms staging POS data into fact_sales with dimension lookups
-- ============================================================================

USE DATABASE DEV_DW;
USE SCHEMA FACTS;

-- ============================================================================
-- Stored Procedure: Load Fact Sales
-- ============================================================================

CREATE OR REPLACE PROCEDURE sp_load_fact_sales()
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
BEGIN
    -- Insert new sales transactions from staging
    INSERT INTO fact_sales (
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
    SELECT DISTINCT
        -- Dimension lookups
        dc.customer_key,
        dp.product_key,
        ds.store_key,
        dd.date_key,
        dt.time_key,
        
        -- Transaction details
        sp.transaction_id,
        sp.transaction_timestamp,
        sp.register_id,
        
        -- Measures
        sp.quantity,
        sp.unit_price,
        sp.discount_amount,
        sp.tax_amount,
        sp.total_amount,
        
        -- Payment information
        sp.payment_method,
        sp.payment_status,
        
        -- Audit columns
        CURRENT_TIMESTAMP() AS created_at,
        CURRENT_TIMESTAMP() AS updated_at,
        'RETAIL_SYSTEM' AS source_system
    FROM DEV_STAGING.SILVER.stg_pos sp
    -- Join to dimensions
    LEFT JOIN DEV_DW.DIMENSIONS.dim_customer dc
        ON sp.customer_id = dc.customer_id
        AND dc.is_current = TRUE
    INNER JOIN DEV_DW.DIMENSIONS.dim_product dp
        ON sp.product_id = dp.product_id
    INNER JOIN DEV_DW.DIMENSIONS.dim_store ds
        ON sp.store_id = ds.store_id
        AND ds.is_current = TRUE
    INNER JOIN DEV_DW.DIMENSIONS.dim_date dd
        ON DATE(sp.transaction_date) = dd.date_value
    LEFT JOIN DEV_DW.DIMENSIONS.dim_time dt
        ON TIME(sp.transaction_time) = dt.time_value
    WHERE sp.is_valid = TRUE
      AND NOT EXISTS (
          SELECT 1
          FROM fact_sales fs
          WHERE fs.transaction_id = sp.transaction_id
            AND fs.product_key = dp.product_key
      );
    
    RETURN 'SUCCESS: Fact sales loaded successfully';
END;
$$;

-- ============================================================================
-- Grant Execute Permission
-- ============================================================================

GRANT USAGE ON PROCEDURE sp_load_fact_sales() TO ROLE DATA_ENGINEER;


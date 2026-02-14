-- ============================================================================
-- SCD Type 2 Load: Customer Dimension
-- Handles historical tracking of customer changes
-- ============================================================================

USE DATABASE DEV_DW;
USE SCHEMA DIMENSIONS;

-- ============================================================================
-- Stored Procedure: Load Customer Dimension (SCD Type 2)
-- ============================================================================

CREATE OR REPLACE PROCEDURE sp_load_dim_customer_scd_type2()
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
BEGIN
    -- Step 1: Close out records that have changed
    UPDATE dim_customer dc
    SET
        effective_to_date = CURRENT_DATE() - 1,
        is_current = FALSE,
        updated_at = CURRENT_TIMESTAMP()
    WHERE dc.is_current = TRUE
      AND EXISTS (
          SELECT 1
          FROM DEV_STAGING.SILVER.stg_customers sc
          WHERE sc.customer_id = dc.customer_id
            AND sc.is_valid = TRUE
            AND (
                -- Check for changes in Type 2 attributes
                COALESCE(sc.first_name, '') != COALESCE(dc.first_name, '')
                OR COALESCE(sc.last_name, '') != COALESCE(dc.last_name, '')
                OR COALESCE(sc.email, '') != COALESCE(dc.email, '')
                OR COALESCE(sc.phone, '') != COALESCE(dc.phone, '')
                OR COALESCE(sc.address_line1, '') != COALESCE(dc.address_line1, '')
                OR COALESCE(sc.city, '') != COALESCE(dc.city, '')
                OR COALESCE(sc.state, '') != COALESCE(dc.state, '')
                OR COALESCE(sc.zip_code, '') != COALESCE(dc.zip_code, '')
                OR COALESCE(sc.customer_segment, '') != COALESCE(dc.customer_segment, '')
            )
      );
    
    -- Step 2: Insert new records for changed customers
    INSERT INTO dim_customer (
        customer_id,
        effective_from_date,
        effective_to_date,
        is_current,
        first_name,
        last_name,
        full_name,
        email,
        phone,
        address_line1,
        address_line2,
        city,
        state,
        zip_code,
        country,
        date_of_birth,
        registration_date,
        customer_segment,
        created_at,
        updated_at,
        source_system
    )
    SELECT DISTINCT
        sc.customer_id,
        CURRENT_DATE() AS effective_from_date,
        NULL AS effective_to_date,
        TRUE AS is_current,
        sc.first_name,
        sc.last_name,
        sc.full_name,
        sc.email,
        sc.phone,
        sc.address_line1,
        sc.address_line2,
        sc.city,
        sc.state,
        sc.zip_code,
        sc.country,
        sc.date_of_birth,
        sc.registration_date,
        sc.customer_segment,
        CURRENT_TIMESTAMP() AS created_at,
        CURRENT_TIMESTAMP() AS updated_at,
        'RETAIL_SYSTEM' AS source_system
    FROM DEV_STAGING.SILVER.stg_customers sc
    WHERE sc.is_valid = TRUE
      AND NOT EXISTS (
          SELECT 1
          FROM dim_customer dc
          WHERE dc.customer_id = sc.customer_id
            AND dc.is_current = TRUE
            AND (
                -- Only insert if there are actual changes
                COALESCE(sc.first_name, '') = COALESCE(dc.first_name, '')
                AND COALESCE(sc.last_name, '') = COALESCE(dc.last_name, '')
                AND COALESCE(sc.email, '') = COALESCE(dc.email, '')
                AND COALESCE(sc.phone, '') = COALESCE(dc.phone, '')
                AND COALESCE(sc.address_line1, '') = COALESCE(dc.address_line1, '')
                AND COALESCE(sc.city, '') = COALESCE(dc.city, '')
                AND COALESCE(sc.state, '') = COALESCE(dc.state, '')
                AND COALESCE(sc.zip_code, '') = COALESCE(dc.zip_code, '')
                AND COALESCE(sc.customer_segment, '') = COALESCE(dc.customer_segment, '')
            )
      )
      AND (
          -- Insert if customer doesn't exist or has changed
          NOT EXISTS (
              SELECT 1
              FROM dim_customer dc
              WHERE dc.customer_id = sc.customer_id
                AND dc.is_current = TRUE
          )
          OR EXISTS (
              SELECT 1
              FROM dim_customer dc
              WHERE dc.customer_id = sc.customer_id
                AND dc.is_current = TRUE
                AND (
                    COALESCE(sc.first_name, '') != COALESCE(dc.first_name, '')
                    OR COALESCE(sc.last_name, '') != COALESCE(dc.last_name, '')
                    OR COALESCE(sc.email, '') != COALESCE(dc.email, '')
                    OR COALESCE(sc.phone, '') != COALESCE(dc.phone, '')
                    OR COALESCE(sc.address_line1, '') != COALESCE(dc.address_line1, '')
                    OR COALESCE(sc.city, '') != COALESCE(dc.city, '')
                    OR COALESCE(sc.state, '') != COALESCE(dc.state, '')
                    OR COALESCE(sc.zip_code, '') != COALESCE(dc.zip_code, '')
                    OR COALESCE(sc.customer_segment, '') != COALESCE(dc.customer_segment, '')
                )
          )
      );
    
    -- Step 3: Insert new customers that don't exist
    INSERT INTO dim_customer (
        customer_id,
        effective_from_date,
        effective_to_date,
        is_current,
        first_name,
        last_name,
        full_name,
        email,
        phone,
        address_line1,
        address_line2,
        city,
        state,
        zip_code,
        country,
        date_of_birth,
        registration_date,
        customer_segment,
        created_at,
        updated_at,
        source_system
    )
    SELECT DISTINCT
        sc.customer_id,
        COALESCE(sc.registration_date, CURRENT_DATE()) AS effective_from_date,
        NULL AS effective_to_date,
        TRUE AS is_current,
        sc.first_name,
        sc.last_name,
        sc.full_name,
        sc.email,
        sc.phone,
        sc.address_line1,
        sc.address_line2,
        sc.city,
        sc.state,
        sc.zip_code,
        sc.country,
        sc.date_of_birth,
        sc.registration_date,
        sc.customer_segment,
        CURRENT_TIMESTAMP() AS created_at,
        CURRENT_TIMESTAMP() AS updated_at,
        'RETAIL_SYSTEM' AS source_system
    FROM DEV_STAGING.SILVER.stg_customers sc
    WHERE sc.is_valid = TRUE
      AND NOT EXISTS (
          SELECT 1
          FROM dim_customer dc
          WHERE dc.customer_id = sc.customer_id
      );
    
    RETURN 'SUCCESS: Customer dimension (SCD Type 2) loaded successfully';
END;
$$;

-- ============================================================================
-- Grant Execute Permission
-- ============================================================================

GRANT USAGE ON PROCEDURE sp_load_dim_customer_scd_type2() TO ROLE DATA_ENGINEER;


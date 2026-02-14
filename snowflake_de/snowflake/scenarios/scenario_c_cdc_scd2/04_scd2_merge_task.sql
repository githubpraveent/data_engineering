-- ============================================================================
-- Scenario C: Historical Data + CDC with SCD Type 2 Dimensions
-- Task/Stored Procedure to MERGE changes into SCD Type 2 dimension
-- ============================================================================

USE DATABASE DEV_DW;
USE SCHEMA DIMENSIONS;

-- ============================================================================
-- Stored Procedure: Load Customer SCD Type 2 from Stream
-- ============================================================================

CREATE OR REPLACE PROCEDURE sp_load_customer_scd2_from_stream()
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
DECLARE
    rows_processed NUMBER;
    current_date_val DATE;
BEGIN
    current_date_val := CURRENT_DATE();
    rows_processed := 0;
    
    -- Step 1: Handle DELETES - Close out records
    UPDATE dim_customers_scd2 dc
    SET
        effective_to_date = :current_date_val - 1,
        is_current = FALSE,
        customer_status = 'INACTIVE',
        updated_at = CURRENT_TIMESTAMP()
    WHERE dc.is_current = TRUE
      AND EXISTS (
          SELECT 1
          FROM DEV_STAGING.STREAMS.stream_customer_changes sc
          WHERE sc.customer_id = dc.customer_id
            AND sc.METADATA$ACTION = 'DELETE'
            AND sc.METADATA$ISUPDATE = FALSE
      );
    
    rows_processed := rows_processed + SQLROWCOUNT;
    
    -- Step 2: Close out records that have changed (for SCD Type 2)
    UPDATE dim_customers_scd2 dc
    SET
        effective_to_date = :current_date_val - 1,
        is_current = FALSE,
        updated_at = CURRENT_TIMESTAMP()
    WHERE dc.is_current = TRUE
      AND EXISTS (
          SELECT 1
          FROM DEV_STAGING.STREAMS.stream_customer_changes sc
          WHERE sc.customer_id = dc.customer_id
            AND sc.METADATA$ACTION = 'INSERT'
            AND sc.METADATA$ISUPDATE = TRUE  -- This indicates an UPDATE
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
    
    rows_processed := rows_processed + SQLROWCOUNT;
    
    -- Step 3: Insert new records for changed customers (SCD Type 2)
    INSERT INTO dim_customers_scd2 (
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
        customer_status,
        source_timestamp,
        created_at,
        updated_at,
        source_system
    )
    SELECT DISTINCT
        sc.customer_id,
        :current_date_val AS effective_from_date,
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
        sc.customer_status,
        sc.source_timestamp,
        CURRENT_TIMESTAMP() AS created_at,
        CURRENT_TIMESTAMP() AS updated_at,
        'CRM_SYSTEM' AS source_system
    FROM DEV_STAGING.STREAMS.stream_customer_changes sc
    WHERE sc.METADATA$ACTION = 'INSERT'
      AND sc.customer_status != 'DELETE'  -- Exclude deleted records (already handled)
      AND NOT EXISTS (
          SELECT 1
          FROM dim_customers_scd2 dc
          WHERE dc.customer_id = sc.customer_id
            AND dc.is_current = TRUE
            AND (
                -- Only insert if there are actual changes
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
      AND (
          -- Insert if customer doesn't exist
          NOT EXISTS (
              SELECT 1
              FROM dim_customers_scd2 dc
              WHERE dc.customer_id = sc.customer_id
          )
          -- Or if current record was closed
          OR EXISTS (
              SELECT 1
              FROM dim_customers_scd2 dc
              WHERE dc.customer_id = sc.customer_id
                AND dc.is_current = TRUE
                AND dc.effective_to_date IS NOT NULL  -- Was just closed
          )
      );
    
    rows_processed := rows_processed + SQLROWCOUNT;
    
    RETURN 'SUCCESS: Processed ' || :rows_processed || ' records. SCD Type 2 load completed.';
END;
$$;

-- ============================================================================
-- Task: Process Customer Changes (Hourly)
-- ============================================================================

USE DATABASE DEV_STAGING;
USE SCHEMA TASKS;

CREATE OR REPLACE TASK task_process_customer_scd2
  WAREHOUSE = WH_TRANS
  SCHEDULE = 'USING CRON 0 * * * * UTC'  -- Every hour
WHEN
  SYSTEM$STREAM_HAS_DATA('DEV_STAGING.STREAMS.stream_customer_changes')
AS
CALL DEV_DW.DIMENSIONS.sp_load_customer_scd2_from_stream();

-- ============================================================================
-- Resume Task
-- ============================================================================

ALTER TASK task_process_customer_scd2 RESUME;

-- ============================================================================
-- Grant Permissions
-- ============================================================================

GRANT USAGE ON PROCEDURE DEV_DW.DIMENSIONS.sp_load_customer_scd2_from_stream() TO ROLE DATA_ENGINEER;
GRANT OPERATE ON TASK DEV_STAGING.TASKS.task_process_customer_scd2 TO ROLE DATA_ENGINEER;


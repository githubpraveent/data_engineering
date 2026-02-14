-- SCD Type 2: Customer Dimension (History)
-- Maintains full history with effective dates and current flag

CREATE OR REPLACE PROCEDURE analytics.sp_scd_type2_customer()
AS $$
DECLARE
    v_effective_date DATE;
    v_rows_updated INTEGER;
    v_rows_inserted INTEGER;
BEGIN
    -- Set effective date to today
    v_effective_date := CURRENT_DATE;

    -- Close existing records that have changed (set end_date and is_current = FALSE)
    UPDATE analytics.dim_customer
    SET
        end_date = v_effective_date - 1,
        is_current = FALSE,
        updated_at = GETDATE()
    FROM staging.customer_batch s
    WHERE analytics.dim_customer.customer_id = s.customer_id
        AND analytics.dim_customer.is_current = TRUE
        AND s.is_valid = TRUE
        AND (
            COALESCE(analytics.dim_customer.customer_name, '') != COALESCE(s.customer_name, '')
            OR COALESCE(analytics.dim_customer.email, '') != COALESCE(s.email, '')
            OR COALESCE(analytics.dim_customer.phone, '') != COALESCE(s.phone, '')
            OR COALESCE(analytics.dim_customer.address, '') != COALESCE(s.address, '')
            OR COALESCE(analytics.dim_customer.city, '') != COALESCE(s.city, '')
            OR COALESCE(analytics.dim_customer.state, '') != COALESCE(s.state, '')
            OR COALESCE(analytics.dim_customer.zip_code, '') != COALESCE(s.zip_code, '')
        );

    GET DIAGNOSTICS v_rows_updated = ROW_COUNT;

    -- Insert new current records for changed customers
    INSERT INTO analytics.dim_customer (
        customer_id,
        customer_name,
        email,
        phone,
        address,
        city,
        state,
        zip_code,
        effective_date,
        end_date,
        is_current,
        created_at,
        updated_at
    )
    SELECT DISTINCT
        s.customer_id,
        s.customer_name,
        s.email,
        s.phone,
        s.address,
        s.city,
        s.state,
        s.zip_code,
        v_effective_date,
        NULL,
        TRUE,
        GETDATE(),
        GETDATE()
    FROM staging.customer_batch s
    WHERE s.is_valid = TRUE
        AND EXISTS (
            SELECT 1
            FROM analytics.dim_customer d
            WHERE d.customer_id = s.customer_id
                AND d.is_current = TRUE
        )
        AND (
            COALESCE((SELECT customer_name FROM analytics.dim_customer WHERE customer_id = s.customer_id AND is_current = TRUE), '') != COALESCE(s.customer_name, '')
            OR COALESCE((SELECT email FROM analytics.dim_customer WHERE customer_id = s.customer_id AND is_current = TRUE), '') != COALESCE(s.email, '')
            OR COALESCE((SELECT phone FROM analytics.dim_customer WHERE customer_id = s.customer_id AND is_current = TRUE), '') != COALESCE(s.phone, '')
            OR COALESCE((SELECT address FROM analytics.dim_customer WHERE customer_id = s.customer_id AND is_current = TRUE), '') != COALESCE(s.address, '')
            OR COALESCE((SELECT city FROM analytics.dim_customer WHERE customer_id = s.customer_id AND is_current = TRUE), '') != COALESCE(s.city, '')
            OR COALESCE((SELECT state FROM analytics.dim_customer WHERE customer_id = s.customer_id AND is_current = TRUE), '') != COALESCE(s.state, '')
            OR COALESCE((SELECT zip_code FROM analytics.dim_customer WHERE customer_id = s.customer_id AND is_current = TRUE), '') != COALESCE(s.zip_code, '')
        );

    GET DIAGNOSTICS v_rows_inserted = ROW_COUNT;

    -- Insert new customers (first time)
    INSERT INTO analytics.dim_customer (
        customer_id,
        customer_name,
        email,
        phone,
        address,
        city,
        state,
        zip_code,
        effective_date,
        end_date,
        is_current,
        created_at,
        updated_at
    )
    SELECT
        s.customer_id,
        s.customer_name,
        s.email,
        s.phone,
        s.address,
        s.city,
        s.state,
        s.zip_code,
        COALESCE(s.created_at::DATE, v_effective_date),
        NULL,
        TRUE,
        GETDATE(),
        GETDATE()
    FROM staging.customer_batch s
    WHERE s.is_valid = TRUE
        AND NOT EXISTS (
            SELECT 1
            FROM analytics.dim_customer d
            WHERE d.customer_id = s.customer_id
        );

    -- Log results
    RAISE NOTICE 'SCD Type 2 Customer: Closed % records, Inserted % new current records, Inserted % new customers',
        v_rows_updated,
        v_rows_inserted,
        (SELECT COUNT(*) FROM staging.customer_batch WHERE is_valid = TRUE AND customer_id NOT IN (SELECT customer_id FROM analytics.dim_customer));
END;
$$ LANGUAGE plpgsql;

-- Grant execute permission
GRANT EXECUTE ON PROCEDURE analytics.sp_scd_type2_customer() TO PUBLIC;


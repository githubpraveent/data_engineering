-- Load Sales Fact Table
-- Incremental load from staging tables

CREATE OR REPLACE PROCEDURE analytics.sp_load_sales_fact()
AS $$
DECLARE
    v_max_order_date TIMESTAMP;
    v_rows_inserted INTEGER;
BEGIN
    -- Get maximum order date already loaded
    SELECT COALESCE(MAX(order_date), '1900-01-01'::TIMESTAMP)
    INTO v_max_order_date
    FROM analytics.fact_sales;

    -- Insert new sales records
    INSERT INTO analytics.fact_sales (
        order_id,
        customer_sk,
        product_sk,
        order_date_key,
        order_date,
        quantity,
        unit_price,
        sales_amount,
        discount_amount,
        net_sales_amount,
        order_status,
        created_at
    )
    SELECT DISTINCT
        o.order_id,
        dc.customer_sk,
        dp.product_sk,
        dd.date_key,
        o.order_date,
        oi.quantity,
        oi.unit_price,
        oi.total_price AS sales_amount,
        0 AS discount_amount,  -- Calculate if discount data available
        oi.total_price AS net_sales_amount,
        o.status AS order_status,
        GETDATE()
    FROM staging.order_batch o
    INNER JOIN staging.order_item_batch oi ON o.order_id = oi.order_id
    INNER JOIN analytics.dim_customer dc ON o.customer_id = dc.customer_id AND dc.is_current = TRUE
    INNER JOIN analytics.dim_product dp ON oi.product_id = dp.product_id
    INNER JOIN analytics.dim_date dd ON o.order_date::DATE = dd.date
    WHERE o.is_valid = TRUE
        AND oi.is_valid = TRUE
        AND o.order_date > v_max_order_date
        AND NOT EXISTS (
            SELECT 1
            FROM analytics.fact_sales fs
            WHERE fs.order_id = o.order_id
                AND fs.product_sk = dp.product_sk
        );

    GET DIAGNOSTICS v_rows_inserted = ROW_COUNT;

    -- Log results
    RAISE NOTICE 'Sales Fact: Inserted % new records', v_rows_inserted;

    -- Update statistics
    ANALYZE analytics.fact_sales;
END;
$$ LANGUAGE plpgsql;

-- Grant execute permission
GRANT EXECUTE ON PROCEDURE analytics.sp_load_sales_fact() TO PUBLIC;


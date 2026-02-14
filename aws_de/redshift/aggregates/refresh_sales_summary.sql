-- Refresh Sales Summary Aggregate Table
-- Daily aggregation of sales facts

CREATE OR REPLACE PROCEDURE analytics.sp_refresh_sales_summary()
AS $$
BEGIN
    -- Delete existing summary for dates that will be refreshed
    DELETE FROM analytics.fact_sales_summary
    WHERE summary_date_key IN (
        SELECT DISTINCT order_date_key
        FROM analytics.fact_sales
        WHERE order_date >= CURRENT_DATE - 7  -- Refresh last 7 days
    );

    -- Insert aggregated sales data
    INSERT INTO analytics.fact_sales_summary (
        summary_date_key,
        customer_sk,
        product_sk,
        total_orders,
        total_quantity,
        total_sales_amount,
        total_discount_amount,
        total_net_sales_amount,
        created_at,
        updated_at
    )
    SELECT
        fs.order_date_key,
        fs.customer_sk,
        fs.product_sk,
        COUNT(DISTINCT fs.order_id) AS total_orders,
        SUM(fs.quantity) AS total_quantity,
        SUM(fs.sales_amount) AS total_sales_amount,
        SUM(fs.discount_amount) AS total_discount_amount,
        SUM(fs.net_sales_amount) AS total_net_sales_amount,
        GETDATE(),
        GETDATE()
    FROM analytics.fact_sales fs
    WHERE fs.order_date >= CURRENT_DATE - 7
    GROUP BY
        fs.order_date_key,
        fs.customer_sk,
        fs.product_sk;

    -- Update statistics
    ANALYZE analytics.fact_sales_summary;

    RAISE NOTICE 'Sales Summary: Refreshed aggregate data for last 7 days';
END;
$$ LANGUAGE plpgsql;

-- Grant execute permission
GRANT EXECUTE ON PROCEDURE analytics.sp_refresh_sales_summary() TO PUBLIC;


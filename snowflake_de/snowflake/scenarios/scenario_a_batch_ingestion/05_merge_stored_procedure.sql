-- ============================================================================
-- Scenario A: Batch Data Ingestion - MERGE Stored Procedure
-- Deduplicates and upserts sales data into warehouse table
-- ============================================================================

USE DATABASE DEV_DW;
USE SCHEMA FACTS;

-- ============================================================================
-- Stored Procedure: Merge Raw Sales into Warehouse
-- ============================================================================

CREATE OR REPLACE PROCEDURE sp_merge_sales_to_warehouse(
    batch_date DATE DEFAULT CURRENT_DATE()
)
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
DECLARE
    merge_start_time TIMESTAMP_NTZ;
    merge_end_time TIMESTAMP_NTZ;
    rows_inserted NUMBER;
    rows_updated NUMBER;
    batch_id VARCHAR(100);
BEGIN
    merge_start_time := CURRENT_TIMESTAMP();
    batch_id := 'BATCH_' || TO_CHAR(merge_start_time, 'YYYYMMDDHH24MISS');
    
    -- MERGE statement to deduplicate and upsert
    MERGE INTO warehouse_sales ws
    USING (
        SELECT DISTINCT
            transaction_id,
            product_id,
            transaction_date,
            transaction_timestamp,
            store_id,
            store_name,
            customer_id,
            customer_name,
            product_sku,
            product_name,
            quantity,
            unit_price,
            discount_amount,
            tax_amount,
            total_amount,
            payment_method,
            payment_status,
            sales_channel,
            promotion_code,
            file_name,
            load_timestamp
        FROM DEV_RAW.BRONZE.raw_sales
        WHERE DATE(load_timestamp) = :batch_date
          AND transaction_id IS NOT NULL
          AND product_id IS NOT NULL
    ) rs
    ON ws.transaction_id = rs.transaction_id 
       AND ws.product_id = rs.product_id
    WHEN MATCHED THEN
        UPDATE SET
            transaction_date = rs.transaction_date,
            transaction_timestamp = rs.transaction_timestamp,
            store_id = rs.store_id,
            store_name = rs.store_name,
            customer_id = rs.customer_id,
            customer_name = rs.customer_name,
            product_sku = rs.product_sku,
            product_name = rs.product_name,
            quantity = rs.quantity,
            unit_price = rs.unit_price,
            discount_amount = rs.discount_amount,
            tax_amount = rs.tax_amount,
            total_amount = rs.total_amount,
            payment_method = rs.payment_method,
            payment_status = rs.payment_status,
            sales_channel = rs.sales_channel,
            promotion_code = rs.promotion_code,
            source_file_name = rs.file_name,
            load_batch_id = :batch_id,
            load_timestamp = rs.load_timestamp,
            updated_at = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN
        INSERT (
            transaction_id,
            product_id,
            transaction_date,
            transaction_timestamp,
            store_id,
            store_name,
            customer_id,
            customer_name,
            product_sku,
            product_name,
            quantity,
            unit_price,
            discount_amount,
            tax_amount,
            total_amount,
            payment_method,
            payment_status,
            sales_channel,
            promotion_code,
            source_file_name,
            load_batch_id,
            load_timestamp,
            created_at,
            updated_at
        )
        VALUES (
            rs.transaction_id,
            rs.product_id,
            rs.transaction_date,
            rs.transaction_timestamp,
            rs.store_id,
            rs.store_name,
            rs.customer_id,
            rs.customer_name,
            rs.product_sku,
            rs.product_name,
            rs.quantity,
            rs.unit_price,
            rs.discount_amount,
            rs.tax_amount,
            rs.total_amount,
            rs.payment_method,
            rs.payment_status,
            rs.sales_channel,
            rs.promotion_code,
            rs.file_name,
            :batch_id,
            rs.load_timestamp,
            CURRENT_TIMESTAMP(),
            CURRENT_TIMESTAMP()
        );
    
    -- Get merge statistics
    rows_inserted := SQLROWCOUNT;
    merge_end_time := CURRENT_TIMESTAMP();
    
    RETURN 'SUCCESS: Merged sales data. Batch ID: ' || :batch_id || 
           ', Rows processed: ' || :rows_inserted || 
           ', Duration: ' || DATEDIFF(second, :merge_start_time, :merge_end_time) || ' seconds';
END;
$$;

-- ============================================================================
-- Grant Execute Permission
-- ============================================================================

GRANT USAGE ON PROCEDURE sp_merge_sales_to_warehouse(DATE) TO ROLE DATA_ENGINEER;


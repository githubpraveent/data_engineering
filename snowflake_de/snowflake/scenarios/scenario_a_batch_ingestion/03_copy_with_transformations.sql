-- ============================================================================
-- Scenario A: Batch Data Ingestion - COPY INTO with Transformations
-- Loads data from external stage with inline transformations
-- ============================================================================

USE DATABASE DEV_RAW;
USE SCHEMA BRONZE;

-- ============================================================================
-- COPY INTO with Transformations
-- This script demonstrates loading with transformations applied during load
-- ============================================================================

COPY INTO raw_sales (
    -- Map columns with transformations
    transaction_id,
    transaction_date,
    transaction_time,
    transaction_timestamp,
    store_id,
    store_name,
    customer_id,
    customer_name,
    product_id,
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
    file_row_number,
    load_timestamp
)
FROM (
    SELECT 
        -- Required fields with validation
        TRIM($1)::VARCHAR(100) AS transaction_id,
        TRY_TO_DATE($2, 'YYYY-MM-DD') AS transaction_date,
        TRY_TO_TIME($3) AS transaction_time,
        TRY_TO_TIMESTAMP_NTZ($2 || ' ' || $3, 'YYYY-MM-DD HH24:MI:SS') AS transaction_timestamp,
        
        -- Store information (trimmed and upper case)
        TRIM(UPPER($4))::VARCHAR(50) AS store_id,
        TRIM($5)::VARCHAR(255) AS store_name,
        
        -- Customer information (nullable)
        NULLIF(TRIM($6), '')::VARCHAR(100) AS customer_id,
        NULLIF(TRIM($7), '')::VARCHAR(255) AS customer_name,
        
        -- Product information
        TRIM(UPPER($8))::VARCHAR(100) AS product_id,
        TRIM($9)::VARCHAR(100) AS product_sku,
        TRIM($10)::VARCHAR(255) AS product_name,
        
        -- Numeric fields with validation
        TRY_TO_NUMBER($11, 10, 2) AS quantity,
        TRY_TO_NUMBER($12, 10, 2) AS unit_price,
        COALESCE(TRY_TO_NUMBER($13, 10, 2), 0) AS discount_amount,
        COALESCE(TRY_TO_NUMBER($14, 10, 2), 0) AS tax_amount,
        TRY_TO_NUMBER($15, 10, 2) AS total_amount,
        
        -- Payment information
        TRIM(UPPER($16))::VARCHAR(50) AS payment_method,
        TRIM(UPPER($17))::VARCHAR(50) AS payment_status,
        
        -- Additional fields
        TRIM(UPPER($18))::VARCHAR(50) AS sales_channel,
        NULLIF(TRIM($19), '')::VARCHAR(50) AS promotion_code,
        
        -- Metadata
        METADATA$FILENAME AS file_name,
        METADATA$FILE_ROW_NUMBER AS file_row_number,
        CURRENT_TIMESTAMP() AS load_timestamp
    FROM @stage_sales_batch
    WHERE $1 IS NOT NULL  -- Skip rows with null transaction_id
      AND TRY_TO_NUMBER($11, 10, 2) > 0  -- Only valid quantities
      AND TRY_TO_NUMBER($12, 10, 2) >= 0  -- Non-negative prices
)
FILE_FORMAT = (
    TYPE = 'CSV'
    FIELD_DELIMITER = ','
    RECORD_DELIMITER = '\n'
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    TRIM_SPACE = TRUE
    ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE
    NULL_IF = ('NULL', 'null', '')
)
ON_ERROR = 'CONTINUE'  -- Continue on errors, log them
FORCE = FALSE  -- Don't reload files already loaded
PURGE = FALSE;  -- Don't delete source files after load

-- ============================================================================
-- Example: Load specific files
-- ============================================================================

-- COPY INTO raw_sales (...)
-- FROM @stage_sales_batch
-- FILES = ('sales_2024-01-15.csv', 'sales_2024-01-16.csv')
-- ... (same column mapping as above)

-- ============================================================================
-- Example: Load files matching a pattern
-- ============================================================================

-- COPY INTO raw_sales (...)
-- FROM @stage_sales_batch
-- PATTERN = '.*sales_2024-01.*\\.csv'
-- ... (same column mapping as above)


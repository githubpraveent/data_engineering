-- ============================================================================
-- Scenario A: Batch Data Ingestion from Cloud Storage
-- Creates external stage for daily sales CSV files from S3
-- ============================================================================

USE DATABASE DEV_RAW;
USE SCHEMA BRONZE;

-- ============================================================================
-- Create External Stage for Sales Data
-- ============================================================================

CREATE OR REPLACE STAGE IF NOT EXISTS stage_sales_batch
  URL = 's3://your-bucket/daily-sales/'
  -- STORAGE_INTEGRATION = s3_integration  -- Uncomment if using storage integration
  FILE_FORMAT = (
    TYPE = 'CSV'
    FIELD_DELIMITER = ','
    RECORD_DELIMITER = '\n'
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    TRIM_SPACE = TRUE
    ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE
    ESCAPE = 'NONE'
    ESCAPE_UNENCLOSED_FIELD = '\134'
    DATE_FORMAT = 'AUTO'
    TIMESTAMP_FORMAT = 'AUTO'
    NULL_IF = ('NULL', 'null', '')
  )
  COMMENT = 'External stage for batch daily sales CSV files';

-- ============================================================================
-- Grant Permissions
-- ============================================================================

GRANT USAGE ON STAGE DEV_RAW.BRONZE.stage_sales_batch TO ROLE DATA_ENGINEER;
GRANT READ ON STAGE DEV_RAW.BRONZE.stage_sales_batch TO ROLE DATA_ENGINEER;


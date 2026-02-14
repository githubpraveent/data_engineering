-- ============================================================================
-- External Stage Setup
-- Creates external stages for cloud object storage integration
-- ============================================================================

-- ============================================================================
-- Storage Integration (one-time setup per cloud provider)
-- ============================================================================

-- AWS S3 Storage Integration
-- Note: Replace with your actual storage integration name and credentials
-- CREATE STORAGE INTEGRATION IF NOT EXISTS s3_integration
--   TYPE = EXTERNAL_STAGE
--   STORAGE_PROVIDER = 'S3'
--   STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::123456789012:role/snowflake-role'
--   ENABLED = TRUE
--   STORAGE_AWS_EXTERNAL_ID = 'SNOWFLAKE_EXTERNAL_ID'
--   STORAGE_ALLOWED_LOCATIONS = ('s3://your-bucket/raw/');

-- Azure Blob Storage Integration
-- CREATE STORAGE INTEGRATION IF NOT EXISTS azure_integration
--   TYPE = EXTERNAL_STAGE
--   STORAGE_PROVIDER = 'AZURE'
--   ENABLED = TRUE
--   AZURE_TENANT_ID = 'your-tenant-id'
--   STORAGE_ALLOWED_LOCATIONS = ('azure://your-account.blob.core.windows.net/raw/');

-- GCS Storage Integration
-- CREATE STORAGE INTEGRATION IF NOT EXISTS gcs_integration
--   TYPE = EXTERNAL_STAGE
--   STORAGE_PROVIDER = 'GCS'
--   ENABLED = TRUE
--   STORAGE_ALLOWED_LOCATIONS = ('gcs://your-bucket/raw/');

-- ============================================================================
-- External Stages for DEV Environment
-- ============================================================================

USE DATABASE DEV_RAW;
USE SCHEMA BRONZE;

-- POS data external stage
CREATE OR REPLACE STAGE IF NOT EXISTS stage_pos_data
  URL = 's3://your-bucket/raw/pos/'
  -- STORAGE_INTEGRATION = s3_integration
  FILE_FORMAT = (TYPE = 'CSV' FIELD_DELIMITER = ',' SKIP_HEADER = 1)
  COMMENT = 'External stage for POS system data';

-- Orders data external stage
CREATE OR REPLACE STAGE IF NOT EXISTS stage_orders_data
  URL = 's3://your-bucket/raw/orders/'
  -- STORAGE_INTEGRATION = s3_integration
  FILE_FORMAT = (TYPE = 'JSON')
  COMMENT = 'External stage for orders system data';

-- Inventory data external stage
CREATE OR REPLACE STAGE IF NOT EXISTS stage_inventory_data
  URL = 's3://your-bucket/raw/inventory/'
  -- STORAGE_INTEGRATION = s3_integration
  FILE_FORMAT = (TYPE = 'CSV' FIELD_DELIMITER = ',' SKIP_HEADER = 1)
  COMMENT = 'External stage for inventory system data';

-- ============================================================================
-- External Stages for QA Environment
-- ============================================================================

USE DATABASE QA_RAW;
USE SCHEMA BRONZE;

CREATE OR REPLACE STAGE IF NOT EXISTS stage_pos_data
  URL = 's3://your-bucket-qa/raw/pos/'
  FILE_FORMAT = (TYPE = 'CSV' FIELD_DELIMITER = ',' SKIP_HEADER = 1)
  COMMENT = 'External stage for POS system data (QA)';

CREATE OR REPLACE STAGE IF NOT EXISTS stage_orders_data
  URL = 's3://your-bucket-qa/raw/orders/'
  FILE_FORMAT = (TYPE = 'JSON')
  COMMENT = 'External stage for orders system data (QA)';

CREATE OR REPLACE STAGE IF NOT EXISTS stage_inventory_data
  URL = 's3://your-bucket-qa/raw/inventory/'
  FILE_FORMAT = (TYPE = 'CSV' FIELD_DELIMITER = ',' SKIP_HEADER = 1)
  COMMENT = 'External stage for inventory system data (QA)';

-- ============================================================================
-- External Stages for PROD Environment
-- ============================================================================

USE DATABASE PROD_RAW;
USE SCHEMA BRONZE;

CREATE OR REPLACE STAGE IF NOT EXISTS stage_pos_data
  URL = 's3://your-bucket-prod/raw/pos/'
  FILE_FORMAT = (TYPE = 'CSV' FIELD_DELIMITER = ',' SKIP_HEADER = 1)
  COMMENT = 'External stage for POS system data (PROD)';

CREATE OR REPLACE STAGE IF NOT EXISTS stage_orders_data
  URL = 's3://your-bucket-prod/raw/orders/'
  FILE_FORMAT = (TYPE = 'JSON')
  COMMENT = 'External stage for orders system data (PROD)';

CREATE OR REPLACE STAGE IF NOT EXISTS stage_inventory_data
  URL = 's3://your-bucket-prod/raw/inventory/'
  FILE_FORMAT = (TYPE = 'CSV' FIELD_DELIMITER = ',' SKIP_HEADER = 1)
  COMMENT = 'External stage for inventory system data (PROD)';

-- ============================================================================
-- Grant Permissions
-- ============================================================================

GRANT USAGE ON STAGE DEV_RAW.BRONZE.stage_pos_data TO ROLE DATA_ENGINEER;
GRANT USAGE ON STAGE DEV_RAW.BRONZE.stage_orders_data TO ROLE DATA_ENGINEER;
GRANT USAGE ON STAGE DEV_RAW.BRONZE.stage_inventory_data TO ROLE DATA_ENGINEER;


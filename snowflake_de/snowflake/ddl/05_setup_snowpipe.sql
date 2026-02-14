-- ============================================================================
-- Snowpipe Setup
-- Creates Snowpipe for automated continuous data ingestion
-- ============================================================================

-- ============================================================================
-- File Formats
-- ============================================================================

USE DATABASE DEV_RAW;
USE SCHEMA BRONZE;

-- CSV file format
CREATE OR REPLACE FILE FORMAT IF NOT EXISTS csv_format
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
  COMMENT = 'CSV file format for raw data ingestion';

-- JSON file format
CREATE OR REPLACE FILE FORMAT IF NOT EXISTS json_format
  TYPE = 'JSON'
  STRIP_OUTER_ARRAY = TRUE
  COMMENT = 'JSON file format for raw data ingestion';

-- ============================================================================
-- Snowpipe for POS Data (DEV)
-- ============================================================================

-- Create pipe for POS data
CREATE OR REPLACE PIPE IF NOT EXISTS pipe_pos_data
  AUTO_INGEST = TRUE
  AS
  COPY INTO DEV_RAW.BRONZE.raw_pos
  FROM @DEV_RAW.BRONZE.stage_pos_data
  FILE_FORMAT = (FORMAT_NAME = 'csv_format')
  PATTERN = '.*pos.*\\.csv'
  ON_ERROR = 'CONTINUE';

-- ============================================================================
-- Snowpipe for Orders Data (DEV)
-- ============================================================================

-- Create pipe for Orders data
CREATE OR REPLACE PIPE IF NOT EXISTS pipe_orders_data
  AUTO_INGEST = TRUE
  AS
  COPY INTO DEV_RAW.BRONZE.raw_orders
  FROM @DEV_RAW.BRONZE.stage_orders_data
  FILE_FORMAT = (FORMAT_NAME = 'json_format')
  PATTERN = '.*orders.*\\.json'
  ON_ERROR = 'CONTINUE';

-- ============================================================================
-- Snowpipe for Inventory Data (DEV)
-- ============================================================================

-- Create pipe for Inventory data
CREATE OR REPLACE PIPE IF NOT EXISTS pipe_inventory_data
  AUTO_INGEST = TRUE
  AS
  COPY INTO DEV_RAW.BRONZE.raw_inventory
  FROM @DEV_RAW.BRONZE.stage_inventory_data
  FILE_FORMAT = (FORMAT_NAME = 'csv_format')
  PATTERN = '.*inventory.*\\.csv'
  ON_ERROR = 'CONTINUE';

-- ============================================================================
-- Grant Permissions
-- ============================================================================

GRANT OWNERSHIP ON PIPE DEV_RAW.BRONZE.pipe_pos_data TO ROLE DATA_ENGINEER;
GRANT OWNERSHIP ON PIPE DEV_RAW.BRONZE.pipe_orders_data TO ROLE DATA_ENGINEER;
GRANT OWNERSHIP ON PIPE DEV_RAW.BRONZE.pipe_inventory_data TO ROLE DATA_ENGINEER;

-- ============================================================================
-- Note: For QA and PROD environments, create similar pipes with appropriate
-- database and stage references. Use environment-specific naming conventions.
-- ============================================================================


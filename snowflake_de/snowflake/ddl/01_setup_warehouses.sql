-- ============================================================================
-- Snowflake Warehouse Setup
-- Creates virtual warehouses for different workloads
-- ============================================================================

-- Warehouse for data ingestion
CREATE WAREHOUSE IF NOT EXISTS WH_INGEST
WITH
    WAREHOUSE_SIZE = 'SMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Warehouse for data ingestion workloads';

-- Warehouse for transformations
CREATE WAREHOUSE IF NOT EXISTS WH_TRANS
WITH
    WAREHOUSE_SIZE = 'MEDIUM'
    AUTO_SUSPEND = 300
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Warehouse for transformation workloads';

-- Warehouse for analytics
CREATE WAREHOUSE IF NOT EXISTS WH_ANALYT
WITH
    WAREHOUSE_SIZE = 'LARGE'
    AUTO_SUSPEND = 600
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Warehouse for analytics and reporting workloads';

-- Warehouse for bulk loading
CREATE WAREHOUSE IF NOT EXISTS WH_LOAD
WITH
    WAREHOUSE_SIZE = 'X-LARGE'
    AUTO_SUSPEND = 300
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Warehouse for bulk data loading operations';

-- Grant usage to appropriate roles
GRANT USAGE ON WAREHOUSE WH_INGEST TO ROLE DATA_ENGINEER;
GRANT USAGE ON WAREHOUSE WH_TRANS TO ROLE DATA_ENGINEER;
GRANT USAGE ON WAREHOUSE WH_ANALYT TO ROLE DATA_ANALYST;
GRANT USAGE ON WAREHOUSE WH_LOAD TO ROLE DATA_ENGINEER;


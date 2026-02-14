-- ============================================================================
-- Scenario A: Batch Data Ingestion - Scheduled Task
-- Creates a Snowflake Task to run the merge procedure hourly
-- ============================================================================

USE DATABASE DEV_DW;
USE SCHEMA FACTS;

-- ============================================================================
-- Task: Merge Sales to Warehouse (Hourly)
-- ============================================================================

CREATE OR REPLACE TASK task_merge_sales_to_warehouse
  WAREHOUSE = WH_TRANS
  SCHEDULE = 'USING CRON 0 * * * * UTC'  -- Every hour at minute 0
  COMMENT = 'Hourly task to merge raw sales data into warehouse table'
AS
CALL DEV_DW.FACTS.sp_merge_sales_to_warehouse(CURRENT_DATE());

-- ============================================================================
-- Resume Task (tasks are created in suspended state by default)
-- ============================================================================

ALTER TASK task_merge_sales_to_warehouse RESUME;

-- ============================================================================
-- Grant Permissions
-- ============================================================================

GRANT OPERATE ON TASK DEV_DW.FACTS.task_merge_sales_to_warehouse TO ROLE DATA_ENGINEER;

-- ============================================================================
-- Example: Task with condition (only run if new data exists)
-- ============================================================================

-- CREATE OR REPLACE TASK task_merge_sales_to_warehouse_conditional
--   WAREHOUSE = WH_TRANS
--   SCHEDULE = 'USING CRON 0 * * * * UTC'
-- WHEN
--   (SELECT COUNT(*) FROM DEV_RAW.BRONZE.raw_sales 
--    WHERE DATE(load_timestamp) = CURRENT_DATE()) > 0
-- AS
-- CALL DEV_DW.FACTS.sp_merge_sales_to_warehouse(CURRENT_DATE());


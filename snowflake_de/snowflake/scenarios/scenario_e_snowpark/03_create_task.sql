-- ============================================================================
-- Scenario E: Data Engineering With Snowpark
-- Creates task to run Snowpark feature engineering on schedule
-- ============================================================================

USE DATABASE DEV_STAGING;
USE SCHEMA TASKS;

-- ============================================================================
-- Task: Compute Customer Features (Daily)
-- ============================================================================

CREATE OR REPLACE TASK task_compute_customer_features
  WAREHOUSE = WH_TRANS
  SCHEDULE = 'USING CRON 0 2 * * * UTC'  -- Daily at 2 AM UTC
  COMMENT = 'Daily task to compute customer features using Snowpark'
AS
CALL DEV_DW.DIMENSIONS.sp_compute_customer_features();

-- ============================================================================
-- Task: Incremental Feature Computation (Hourly)
-- Processes only new/changed customers using streams
-- ============================================================================

CREATE OR REPLACE TASK task_compute_customer_features_incremental
  WAREHOUSE = WH_TRANS
  SCHEDULE = 'USING CRON 0 * * * * UTC'  -- Every hour
WHEN
  SYSTEM$STREAM_HAS_DATA('DEV_STAGING.STREAMS.stream_customer_changes')
  AND (SELECT COUNT(*) FROM DEV_STAGING.STREAMS.stream_customer_changes) > 0
AS
CALL DEV_DW.DIMENSIONS.sp_compute_customer_features_incremental();

-- ============================================================================
-- Resume Tasks
-- ============================================================================

ALTER TASK task_compute_customer_features RESUME;
ALTER TASK task_compute_customer_features_incremental RESUME;

-- ============================================================================
-- Grant Permissions
-- ============================================================================

GRANT OPERATE ON TASK DEV_STAGING.TASKS.task_compute_customer_features TO ROLE DATA_ENGINEER;
GRANT OPERATE ON TASK DEV_STAGING.TASKS.task_compute_customer_features_incremental TO ROLE DATA_ENGINEER;


# Operational Runbook

## Table of Contents
1. [Environment Management](#environment-management)
2. [Pipeline Operations](#pipeline-operations)
3. [Failure Recovery](#failure-recovery)
4. [Data Backfill](#data-backfill)
5. [Schema Changes](#schema-changes)
6. [Performance Tuning](#performance-tuning)
7. [Monitoring and Alerts](#monitoring-and-alerts)

## Environment Management

### Creating a New Environment

1. **Clone Production Database (Zero-Copy Cloning)**
   ```sql
   CREATE DATABASE QA_RAW CLONE PROD_RAW;
   CREATE DATABASE QA_STAGING CLONE PROD_STAGING;
   CREATE DATABASE QA_DW CLONE PROD_DW;
   ```

2. **Update Environment-Specific Configuration**
   - Update Airflow variables for the new environment
   - Configure environment-specific Snowflake connections
   - Update external stage URLs if needed

3. **Verify Environment**
   ```sql
   -- Check database existence
   SHOW DATABASES LIKE 'QA_%';
   
   -- Verify schemas
   SHOW SCHEMAS IN DATABASE QA_RAW;
   ```

### Promoting Code Across Environments

1. **Development → QA**
   ```bash
   # Merge dev branch to qa branch
   git checkout qa
   git merge dev
   git push origin qa
   # CI/CD pipeline will automatically deploy to QA
   ```

2. **QA → Production**
   ```bash
   # After QA approval, merge to main
   git checkout main
   git merge qa
   git push origin main
   # CI/CD pipeline will deploy to production (with approval)
   ```

## Pipeline Operations

### Starting a Pipeline Manually

1. **Via Airflow UI**
   - Navigate to DAGs page
   - Select the DAG
   - Click "Trigger DAG"

2. **Via Airflow CLI**
   ```bash
   airflow dags trigger retail_ingestion_pipeline
   ```

### Stopping a Pipeline

1. **Via Airflow UI**
   - Navigate to DAG runs
   - Select the running DAG
   - Click "Clear" or "Mark as Failed"

2. **Via Airflow CLI**
   ```bash
   airflow dags pause retail_ingestion_pipeline
   ```

### Checking Pipeline Status

```sql
-- Check Snowflake task status
SHOW TASKS IN SCHEMA DEV_STAGING.TASKS;

-- Check stream status
SELECT SYSTEM$STREAM_HAS_DATA('DEV_STAGING.STREAMS.stream_pos_changes');

-- Check pipe status
SELECT SYSTEM$PIPE_STATUS('DEV_RAW.BRONZE.pipe_pos_data');
```

## Failure Recovery

### Common Failure Scenarios

#### 1. Snowpipe Ingestion Failure

**Symptoms:**
- No new data in raw tables
- Pipe status shows errors

**Recovery Steps:**
```sql
-- Check pipe status
SELECT SYSTEM$PIPE_STATUS('DEV_RAW.BRONZE.pipe_pos_data');

-- Check for errors
SELECT * FROM TABLE(INFORMATION_SCHEMA.PIPE_USAGE_HISTORY(
    DATE_RANGE_START => DATEADD('hours', -1, CURRENT_TIMESTAMP())
))
WHERE PIPE_NAME = 'PIPE_POS_DATA'
ORDER BY START_TIME DESC;

-- Restart pipe (if needed)
ALTER PIPE DEV_RAW.BRONZE.pipe_pos_data SET PIPE_EXECUTION_PAUSED = FALSE;
```

#### 2. Transformation Task Failure

**Symptoms:**
- Tasks show as suspended or failed
- No data in staging tables

**Recovery Steps:**
```sql
-- Check task execution history
SELECT * FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
    SCHEDULED_TIME_RANGE_START => DATEADD('hours', -1, CURRENT_TIMESTAMP())
))
WHERE NAME = 'TASK_BRONZE_TO_SILVER_POS'
ORDER BY SCHEDULED_TIME DESC;

-- Resume suspended task
ALTER TASK DEV_STAGING.TASKS.task_bronze_to_silver_pos RESUME;

-- Manually execute task
EXECUTE TASK DEV_STAGING.TASKS.task_bronze_to_silver_pos;
```

#### 3. Data Quality Check Failure

**Symptoms:**
- Data quality DAG fails
- Invalid data in tables

**Recovery Steps:**
1. Identify the failing check
2. Query invalid records:
   ```sql
   SELECT * FROM DEV_STAGING.SILVER.stg_pos
   WHERE is_valid = FALSE
   ORDER BY created_at DESC;
   ```
3. Investigate root cause
4. Fix data at source or apply data correction
5. Re-run transformation

#### 4. Dimension Load Failure (SCD Type 2)

**Symptoms:**
- Stored procedure fails
- Dimension table has inconsistent data

**Recovery Steps:**
```sql
-- Check for overlapping effective dates
SELECT customer_id, COUNT(*) as overlapping_records
FROM DEV_DW.DIMENSIONS.dim_customer
GROUP BY customer_id
HAVING COUNT(*) > 1 AND SUM(CASE WHEN is_current = TRUE THEN 1 ELSE 0 END) != 1;

-- Fix overlapping records manually if needed
-- Then re-run stored procedure
CALL DEV_DW.DIMENSIONS.sp_load_dim_customer_scd_type2();
```

### Manual Recovery Procedures

#### Re-running Failed Airflow Tasks

1. **Via Airflow UI:**
   - Navigate to failed task
   - Click "Clear" to reset task state
   - Task will re-run on next DAG run

2. **Via Airflow CLI:**
   ```bash
   airflow tasks clear retail_transformation_pipeline --start-date 2024-01-01 --end-date 2024-01-02
   ```

## Data Backfill

### Backfilling Raw Data

1. **Identify Missing Data Period**
   ```sql
   SELECT 
       DATE(load_timestamp) as load_date,
       COUNT(*) as row_count
   FROM DEV_RAW.BRONZE.raw_pos
   WHERE load_timestamp >= '2024-01-01'
   GROUP BY DATE(load_timestamp)
   ORDER BY load_date;
   ```

2. **Load Historical Files**
   - Place files in appropriate S3/GCS bucket path
   - Snowpipe will automatically ingest
   - Or manually copy into stage:
   ```sql
   COPY INTO DEV_RAW.BRONZE.raw_pos
   FROM @DEV_RAW.BRONZE.stage_pos_data
   FILES = ('historical_file_2024-01-01.csv')
   FILE_FORMAT = (FORMAT_NAME = 'csv_format');
   ```

3. **Trigger Transformation**
   ```sql
   -- Manually execute transformation tasks
   EXECUTE TASK DEV_STAGING.TASKS.task_bronze_to_silver_pos;
   ```

### Backfilling Fact Tables

1. **Clear and Reload Facts**
   ```sql
   -- Delete fact records for the period
   DELETE FROM DEV_DW.FACTS.fact_sales
   WHERE date_key IN (
       SELECT date_key FROM DEV_DW.DIMENSIONS.dim_date
       WHERE date_value BETWEEN '2024-01-01' AND '2024-01-31'
   );
   
   -- Reload facts
   CALL DEV_DW.FACTS.sp_load_fact_sales();
   ```

2. **Incremental Backfill**
   ```sql
   -- Modify stored procedure to process specific date range
   -- Or use Airflow backfill:
   airflow dags backfill retail_transformation_pipeline --start-date 2024-01-01 --end-date 2024-01-31
   ```

## Schema Changes

### Adding a New Column

1. **Development Environment**
   ```sql
   ALTER TABLE DEV_RAW.BRONZE.raw_pos
   ADD COLUMN new_column VARCHAR(100);
   ```

2. **Update Transformation Logic**
   - Update staging table DDL
   - Update transformation SQL
   - Update dimension/fact tables if needed

3. **Test in QA**
   - Apply same changes to QA environment
   - Run test data through pipeline
   - Validate results

4. **Deploy to Production**
   - Apply schema changes during maintenance window
   - Update transformation logic
   - Monitor for issues

### Changing Data Types

1. **Create Migration Script**
   ```sql
   -- Example: Change VARCHAR to NUMBER
   ALTER TABLE DEV_RAW.BRONZE.raw_pos
   ALTER COLUMN quantity TYPE NUMBER(10,2);
   ```

2. **Handle Data Conversion**
   ```sql
   -- Update existing data if needed
   UPDATE DEV_RAW.BRONZE.raw_pos
   SET quantity = TRY_TO_NUMBER(quantity::VARCHAR)
   WHERE quantity IS NOT NULL;
   ```

3. **Update Dependent Objects**
   - Update staging tables
   - Update transformation logic
   - Update fact tables

## Performance Tuning

### Scaling Virtual Warehouses

```sql
-- Scale up warehouse for heavy workload
ALTER WAREHOUSE WH_TRANS SET WAREHOUSE_SIZE = 'LARGE';

-- Scale down after workload completes
ALTER WAREHOUSE WH_TRANS SET WAREHOUSE_SIZE = 'MEDIUM';
```

### Optimizing Clustering

```sql
-- Check clustering effectiveness
SELECT SYSTEM$CLUSTERING_INFORMATION('DEV_DW.FACTS.fact_sales', '(date_key, store_key)');

-- Recluster if needed
ALTER TABLE DEV_DW.FACTS.fact_sales RECLUSTER;
```

### Query Performance

1. **Check Query History**
   ```sql
   SELECT 
       QUERY_TEXT,
       EXECUTION_TIME,
       BYTES_SCANNED,
       ROWS_PRODUCED
   FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
   WHERE QUERY_TEXT LIKE '%fact_sales%'
   ORDER BY EXECUTION_TIME DESC
   LIMIT 10;
   ```

2. **Optimize Slow Queries**
   - Add appropriate indexes
   - Optimize JOIN conditions
   - Use materialized views for common queries

## Monitoring and Alerts

### Key Metrics to Monitor

1. **Data Volume**
   - Row counts per table
   - Data growth trends
   - Unexpected drops in volume

2. **Data Freshness**
   - Time since last load
   - Pipeline execution times
   - Task completion status

3. **Data Quality**
   - Invalid record counts
   - Null value percentages
   - Referential integrity violations

4. **Performance**
   - Query execution times
   - Warehouse utilization
   - Storage costs

### Setting Up Alerts

1. **Airflow Email Alerts**
   - Configured in DAG default_args
   - Sends email on task failure

2. **Snowflake Alerts** (if using Snowflake Alerts)
   ```sql
   CREATE ALERT IF NOT EXISTS alert_data_freshness
   WAREHOUSE = WH_TRANS
   SCHEDULE = 'USING CRON 0 * * * * UTC'
   IF (
       SELECT DATEDIFF(hour, MAX(load_timestamp), CURRENT_TIMESTAMP())
       FROM DEV_RAW.BRONZE.raw_pos
   ) > 2
   THEN
       CALL SYSTEM$SEND_EMAIL('data-engineering@company.com', 'Data Freshness Alert');
   ```

3. **Custom Monitoring Scripts**
   - Create Python scripts to check metrics
   - Schedule via Airflow or cron
   - Send alerts via Slack/email

### Onboarding New Source Systems

1. **Create Raw Tables**
   - Add new table to Bronze layer
   - Define schema based on source

2. **Create Staging Tables**
   - Add new staging table
   - Define transformation logic

3. **Create Dimensions/Facts**
   - Add new dimensions if needed
   - Update or create fact tables

4. **Create Pipeline**
   - Add new Airflow DAG or tasks
   - Configure Snowpipe if needed
   - Set up data quality checks

5. **Test and Validate**
   - Test with sample data
   - Validate transformations
   - Run data quality checks

6. **Deploy**
   - Deploy to Dev → QA → Prod
   - Monitor initial runs
   - Document in metadata

## Emergency Contacts

- **Data Engineering Team**: data-engineering@company.com
- **Snowflake Admin**: snowflake-admin@company.com
- **Airflow Admin**: airflow-admin@company.com
- **On-Call Engineer**: Check PagerDuty/Slack

## Appendix

### Useful Snowflake Queries

```sql
-- Check warehouse status
SHOW WAREHOUSES;

-- Check database sizes
SELECT 
    DATABASE_NAME,
    SUM(BYTES) / (1024*1024*1024) as SIZE_GB
FROM INFORMATION_SCHEMA.TABLE_STORAGE_METRICS
GROUP BY DATABASE_NAME;

-- Check task execution history
SELECT * FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY())
WHERE SCHEDULED_TIME >= CURRENT_TIMESTAMP() - INTERVAL '24 hours'
ORDER BY SCHEDULED_TIME DESC;
```

### Useful Airflow Commands

```bash
# List DAGs
airflow dags list

# Check DAG status
airflow dags state retail_ingestion_pipeline 2024-01-01

# Test a task
airflow tasks test retail_ingestion_pipeline check_snowpipe_status 2024-01-01
```


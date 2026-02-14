# Operational Runbook

## Retail Data Lakehouse - Operational Guide

This runbook provides operational procedures for managing the retail data lakehouse on Databricks.

---

## Table of Contents

1. [Onboarding a New Data Source](#onboarding-a-new-data-source)
2. [Failure Handling](#failure-handling)
3. [Backfilling Data](#backfilling-data)
4. [Scaling and Performance](#scaling-and-performance)
5. [Cost Management](#cost-management)
6. [Troubleshooting](#troubleshooting)
7. [Monitoring](#monitoring)
8. [Disaster Recovery](#disaster-recovery)

---

## Onboarding a New Data Source

### Steps to Add a New Retail Source (e.g., POS System)

1. **Create Bronze Table Schema**
   - Define schema in `databricks/notebooks/utilities/schema_definitions.py`
   - Example: `BRONZE_POS_SCHEMA`

2. **Create Ingestion Notebook**
   - Create `databricks/notebooks/ingestion/batch/ingest_pos.py`
   - Configure source connection (JDBC, file path, etc.)
   - Add ingestion metadata columns
   - Enable Change Data Feed (CDF)

3. **Create Silver Transformation Notebook**
   - Create `databricks/notebooks/transformation/bronze_to_silver/clean_pos.py`
   - Implement data cleaning logic
   - Add validation rules
   - Implement deduplication

4. **Create Gold Transformation Notebook** (if needed)
   - Create dimension or fact table notebooks
   - Implement SCD Type 1 or Type 2 logic

5. **Add Airflow DAG Tasks**
   - Update `airflow/dags/ingestion_dag.py`
   - Add ingestion task
   - Update transformation DAG if needed

6. **Add Data Quality Checks**
   - Update `airflow/dags/data_quality_dag.py`
   - Define quality checks for new tables

7. **Deploy to Dev Environment**
   ```bash
   ./scripts/deploy_notebooks.sh dev
   ```

8. **Test in Dev**
   - Run ingestion job manually
   - Verify Bronze data
   - Run transformations
   - Validate quality checks

9. **Promote to QA**
   - Merge to `qa` branch
   - Deploy to QA environment
   - Run full pipeline

10. **Promote to Prod**
    - Merge to `main` branch
    - Deploy to production
    - Monitor initial runs

---

## Failure Handling

### Spark Job Failures

**Symptoms:**
- Airflow task shows failure status
- Databricks job shows failure
- Error messages in job logs

**Actions:**

1. **Check Databricks Job Logs**
   ```bash
   databricks jobs get-run --run-id <RUN_ID>
   databricks jobs get-run-output --run-id <RUN_ID>
   ```

2. **Common Failure Causes:**
   - **Out of Memory**: Increase cluster size or optimize query
   - **Schema Mismatch**: Check Delta schema evolution settings
   - **Network Issues**: Verify source system connectivity
   - **Data Quality Issues**: Check for nulls, duplicates, invalid data

3. **Retry Strategy:**
   - Airflow automatically retries (3 attempts with exponential backoff)
   - If retries fail, investigate root cause

4. **Manual Retry:**
   ```bash
   # Retry via Databricks CLI
   databricks jobs run-now --job-id <JOB_ID>
   
   # Retry via Airflow UI
   # Click "Clear" on failed task → Re-run
   ```

### Data Quality Check Failures

**Symptoms:**
- Quality check task fails
- Alerts sent to team

**Actions:**

1. **Review Quality Check Results**
   - Check Airflow logs
   - Review quality check metrics in monitoring table

2. **Identify Failed Checks:**
   - Not null violations
   - Duplicate records
   - Referential integrity issues
   - Value range violations

3. **Fix Data Issues:**
   - Backfill corrections
   - Update transformation logic
   - Notify source system team if upstream issue

4. **Re-run Quality Checks:**
   ```bash
   # Re-run quality DAG
   airflow dags trigger retail_data_quality_checks
   ```

### Airflow DAG Failures

**Symptoms:**
- DAG shows failed status
- Tasks marked as failed

**Actions:**

1. **Check Airflow UI**
   - View DAG graph
   - Identify failed tasks
   - Check task logs

2. **Check Dependencies:**
   - Ensure upstream tasks completed
   - Verify task dependencies are correct

3. **Clear and Re-run:**
   - Clear failed task
   - Re-run DAG from failed task

---

## Backfilling Data

### Backfill Bronze Layer

**Scenario**: Need to reload historical data

```python
# In Databricks notebook
# Read historical data from source
df_historical = spark.read \
    .format("jdbc") \
    .option("url", source_url) \
    .option("dbtable", "orders") \
    .option("query", "SELECT * FROM orders WHERE order_date >= '2023-01-01'") \
    .load()

# Write to Bronze (mode: overwrite for specific date range)
df_historical.write \
    .format("delta") \
    .mode("overwrite") \
    .option("replaceWhere", "order_date >= '2023-01-01'") \
    .saveAsTable("retail_datalake.dev_bronze.orders")
```

### Backfill Silver Layer

```python
# Re-run transformation for specific date range
# Update notebook parameter: last_processed_timestamp
dbutils.widgets.text("backfill_start_date", "2023-01-01")
dbutils.widgets.text("backfill_end_date", "2023-12-31")

# In transformation notebook, filter by date range
df_bronze = spark.read.format("delta").table(BRONZE_TABLE) \
    .filter((col("order_date") >= backfill_start_date) & 
            (col("order_date") <= backfill_end_date))

# Merge to Silver (replaceWhere)
df_silver.write \
    .format("delta") \
    .mode("overwrite") \
    .option("replaceWhere", f"order_date >= '{backfill_start_date}' AND order_date <= '{backfill_end_date}'") \
    .saveAsTable(SILVER_TABLE)
```

### Backfill Gold Layer

```python
# Re-run Gold transformations for date range
# Similar approach as Silver backfill
# Use replaceWhere for incremental backfill
```

### Using Time Travel for Backfill

```python
# Query historical version of table
df_historical = spark.read.format("delta") \
    .option("versionAsOf", 10) \
    .table("retail_datalake.dev_silver.orders")

# Or query by timestamp
df_historical = spark.read.format("delta") \
    .option("timestampAsOf", "2023-01-01") \
    .table("retail_datalake.dev_silver.orders")
```

---

## Scaling and Performance

### Sizing Databricks Clusters

**Job Clusters (Batch Processing):**
- **Small jobs** (< 1GB data): 2 workers, i3.xlarge
- **Medium jobs** (1-100GB data): 4-8 workers, i3.xlarge or i3.2xlarge
- **Large jobs** (> 100GB data): 8+ workers, i3.2xlarge or i3.4xlarge

**Interactive Clusters (Ad-hoc Queries):**
- Start with 2-4 workers
- Auto-scaling enabled
- Auto-termination after 30 minutes

**SQL Warehouses:**
- Small: 2-8 DWUs (data warehouse units)
- Medium: 8-32 DWUs
- Large: 32-128 DWUs
- Auto-scaling based on query load

### Optimizing Delta Tables

**File Compaction:**
```sql
OPTIMIZE retail_datalake.prod_gold.fact_sales
```

**Z-Ordering:**
```sql
OPTIMIZE retail_datalake.prod_gold.fact_sales
ZORDER BY (date_key, store_key, product_key)
```

**Vacuum Old Files:**
```sql
VACUUM retail_datalake.prod_gold.fact_sales
RETAIN 168 HOURS  -- Keep 7 days of history
```

**Partitioning:**
- Partition large tables by date (e.g., `date_key`)
- Avoid over-partitioning (too many small files)

### Query Performance Tuning

1. **Use Caching:**
   ```sql
   CACHE TABLE retail_datalake.prod_gold.fact_sales
   ```

2. **Filter Early:**
   - Apply filters before joins
   - Use partition pruning

3. **Avoid Full Table Scans:**
   - Use indexed columns
   - Filter on partition columns

4. **Optimize Joins:**
   - Broadcast small tables
   - Use appropriate join strategies

---

## Cost Management

### Compute Cost Optimization

1. **Use Spot Instances:**
   - Configure in cluster settings
   - Can save 50-90% on compute costs

2. **Auto-termination:**
   - Set clusters to auto-terminate after inactivity
   - Default: 30 minutes

3. **Right-size Clusters:**
   - Don't over-provision
   - Monitor job durations and scale accordingly

4. **Schedule Jobs:**
   - Run during off-peak hours
   - Batch jobs together to share clusters

### Storage Cost Optimization

1. **Vacuum Old Files:**
   ```sql
   VACUUM table_name RETAIN 168 HOURS
   ```

2. **Optimize File Sizes:**
   - Target 128MB-256MB per file
   - Use OPTIMIZE to compact files

3. **Use Lifecycle Policies:**
   - Archive old data to cheaper storage (S3 Glacier)
   - Delete data beyond retention period

### Monitoring Costs

1. **Databricks Cost Dashboard:**
   - View in Databricks UI
   - Track compute and storage costs

2. **Set Budget Alerts:**
   - Configure in Databricks account settings
   - Get alerts when approaching budget

---

## Troubleshooting

### Common Issues

#### Issue: Slow Query Performance

**Diagnosis:**
```sql
-- Check table size
SELECT COUNT(*) FROM retail_datalake.prod_gold.fact_sales;

-- Check file count
DESCRIBE DETAIL retail_datalake.prod_gold.fact_sales;
```

**Solutions:**
- Run OPTIMIZE to compact files
- Add Z-ordering
- Partition large tables
- Increase cluster size

#### Issue: Out of Memory Errors

**Diagnosis:**
- Check Spark executor memory settings
- Review job logs for memory errors

**Solutions:**
- Increase cluster size
- Reduce partition size
- Optimize queries (filter early, broadcast joins)
- Increase executor memory:
  ```python
  spark.conf.set("spark.executor.memory", "16g")
  ```

#### Issue: Schema Evolution Errors

**Diagnosis:**
- Delta schema mismatch errors
- New columns not recognized

**Solutions:**
```python
# Enable schema merging
df.write.format("delta").mode("append") \
    .option("mergeSchema", "true") \
    .saveAsTable(table_name)

# Or explicitly add new columns
df = df.withColumn("new_column", lit(None))
```

#### Issue: Streaming Job Lag

**Diagnosis:**
- Check Kafka lag
- Review streaming query status

**Solutions:**
- Increase cluster size
- Adjust trigger interval
- Optimize streaming queries
- Check checkpoint location

---

## Monitoring

### Airflow Monitoring

1. **DAG Status:**
   - View in Airflow UI
   - Set up Slack/email alerts

2. **Task Metrics:**
   - Task duration
   - Success/failure rates
   - Retry counts

### Databricks Monitoring

1. **Job Monitoring:**
   - Job run history
   - Job duration trends
   - Failure rates

2. **Cluster Monitoring:**
   - Cluster utilization
   - Memory usage
   - CPU usage

3. **Query Performance:**
   - Query duration
   - Data scanned
   - Query plans

### Data Quality Monitoring

1. **Quality Check Results:**
   - Review quality check metrics
   - Track quality trends over time

2. **Data Freshness:**
   - Monitor last update timestamps
   - Alert if data is stale

---

## Disaster Recovery

### Backup Strategy

1. **Delta Lake Time Travel:**
   - Keep 7-30 days of history
   - Can restore to any version

2. **S3 Versioning:**
   - Enable S3 versioning on Delta tables
   - Can restore from S3 versions

3. **Database Backups:**
   - Backup source systems regularly
   - Can re-ingest from backups

### Recovery Procedures

**Scenario: Data Corruption**

1. **Identify Issue:**
   - Check Airflow job failures
   - Review data quality checks

2. **Restore from Time Travel:**
   ```python
   # Restore to previous version
   spark.sql("""
       RESTORE TABLE retail_datalake.prod_gold.fact_sales
       TO VERSION AS OF 10
   """)
   ```

3. **Re-run Transformations:**
   - Re-run affected transformations
   - Validate data quality

**Scenario: Complete Data Loss**

1. **Restore from S3:**
   - Restore S3 bucket to previous state
   - Recreate Delta tables

2. **Re-ingest from Source:**
   - Re-run ingestion jobs
   - Backfill transformations

---

## Contact & Escalation

- **Data Engineering Team**: data-engineering@company.com
- **On-Call Engineer**: See PagerDuty rotation
- **Databricks Support**: support@databricks.com (if on Enterprise plan)

---

## Appendix

### Useful Commands

```bash
# List Databricks jobs
databricks jobs list

# Get job run details
databricks jobs get-run --run-id <RUN_ID>

# Run job manually
databricks jobs run-now --job-id <JOB_ID>

# List Delta table versions
databricks sql execute --query "DESCRIBE HISTORY retail_datalake.prod_gold.fact_sales"

# Optimize table
databricks sql execute --query "OPTIMIZE retail_datalake.prod_gold.fact_sales"
```

### Useful SQL Queries

```sql
-- Check table row count
SELECT COUNT(*) FROM retail_datalake.prod_gold.fact_sales;

-- Check data freshness
SELECT MAX(updated_at) FROM retail_datalake.prod_gold.fact_sales;

-- Check table size
DESCRIBE DETAIL retail_datalake.prod_gold.fact_sales;

-- Check quality issues
SELECT * FROM retail_datalake.prod_monitoring.quality_metrics
WHERE check_status = 'FAILED'
ORDER BY check_timestamp DESC;
```


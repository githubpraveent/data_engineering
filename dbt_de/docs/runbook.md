# Operational Runbook

This runbook provides step-by-step procedures for common operational tasks in the retail data warehouse.

## Table of Contents

1. [Onboarding a New Source System](#onboarding-a-new-source-system)
2. [Failure Handling](#failure-handling)
3. [Backfilling Data](#backfilling-data)
4. [Deploying Changes](#deploying-changes)
5. [Monitoring and Alerts](#monitoring-and-alerts)
6. [Troubleshooting](#troubleshooting)

## Onboarding a New Source System

### Step 1: Define Source in dbt

1. Add source definition to `dbt_project/models/staging/_staging.yml`:
```yaml
sources:
  - name: raw_data
    tables:
      - name: new_source_table
        description: "Description of new source"
        columns:
          - name: id
            tests:
              - unique
              - not_null
```

### Step 2: Create Staging Model

1. Create staging model `dbt_project/models/staging/stg_new_source.sql`:
```sql
{{ config(materialized='view', tags=['staging']) }}

with source as (
    select * from {{ source('raw_data', 'new_source_table') }}
),

cleaned as (
    select
        cast(id as integer) as id,
        -- Add transformations
    from source
)

select * from cleaned
```

### Step 3: Add Tests

1. Add tests to `_staging.yml`:
```yaml
models:
  - name: stg_new_source
    columns:
      - name: id
        tests:
          - unique
          - not_null
```

### Step 4: Create Ingestion Script

1. Create `ingestion/scripts/ingest_new_source.py`
2. Implement extraction, transformation, and loading logic
3. Test script locally

### Step 5: Add to Airflow DAG

1. Add ingestion task to `airflow/dags/data_ingestion.py`:
```python
ingest_new_source = PythonOperator(
    task_id='ingest_new_source',
    python_callable=ingest_new_source_function,
    dag=dag,
)
```

2. Add dependencies:
```python
ingest_new_source >> validate_ingestion_task
```

### Step 6: Create Dimension/Fact Models (if needed)

1. Create dimension models in `dbt_project/models/dimensions/`
2. Create fact models in `dbt_project/models/facts/`
3. Add to appropriate mart models

### Step 7: Test and Deploy

1. Test in dev environment
2. Create PR and run CI/CD
3. Deploy to QA for validation
4. Promote to production

## Failure Handling

### Ingestion DAG Failure

**Symptoms**: Data not appearing in bronze layer, Airflow task marked as failed

**Steps**:
1. Check Airflow logs for the failed task
2. Identify the root cause:
   - Source system unavailable
   - Network issues
   - Authentication failures
   - Data format changes

3. **Retry**:
   ```bash
   # In Airflow UI: Clear task and retry
   # Or via CLI:
   airflow tasks clear data_ingestion_bronze ingest_orders --downstream
   ```

4. **Manual re-run**:
   ```bash
   python ingestion/scripts/ingest_orders.py \
       --start-date 2024-01-01 \
       --end-date 2024-01-01
   ```

5. **If data corruption detected**:
   - Delete corrupted files from bronze layer
   - Re-run ingestion for affected date range

### Transformation DAG Failure

**Symptoms**: dbt models failing, tests failing

**Steps**:
1. Check dbt logs in Airflow task logs
2. Identify failing model:
   ```bash
   cd dbt_project
   dbt run --select <failing_model> --target dev
   ```

3. **Common issues**:
   - **Schema changes**: Update staging model to handle new columns
   - **Data quality**: Fix data issues in source or add data cleaning
   - **Dependencies**: Ensure upstream models completed successfully

4. **Fix and re-run**:
   ```bash
   # Fix the model SQL
   # Re-run from failing model downstream
   dbt run --select <failing_model>+ --target dev
   dbt test --select <failing_model>+ --target dev
   ```

5. **If tests fail**:
   - Review test results
   - Determine if data issue or test issue
   - Fix data or adjust test thresholds

### Data Quality Test Failures

**Symptoms**: dbt tests failing, alerts triggered

**Steps**:
1. Identify failing tests:
   ```bash
   dbt test --select <model> --target dev
   ```

2. **Investigate**:
   - Check test output for specific failures
   - Query data to understand issue
   - Determine if business rule violation or data quality issue

3. **Resolution**:
   - **Data issue**: Fix in source system or add data cleaning
   - **Test issue**: Adjust test logic or thresholds
   - **Business rule change**: Update test to reflect new rules

4. **Document**:
   - Document the issue and resolution
   - Update data quality rules if needed

## Backfilling Data

### Backfilling dbt Models

**Scenario**: New model added or model logic changed, need to rebuild historical data

**Steps**:

1. **Full refresh for new model**:
   ```bash
   cd dbt_project
   dbt run --select <new_model> --full-refresh --target dev
   ```

2. **Incremental backfill**:
   ```bash
   # For incremental models, run for date range
   dbt run --select <incremental_model> \
       --vars '{"start_date": "2024-01-01", "end_date": "2024-12-31"}' \
       --target dev
   ```

3. **Backfill in production**:
   - Test in dev/QA first
   - Schedule maintenance window if large backfill
   - Run during low-traffic period
   - Monitor warehouse costs

4. **SCD Type 2 backfill**:
   ```bash
   # SCD Type 2 dimensions need special handling
   # May need to rebuild from scratch
   dbt run --select dim_customers --full-refresh --target prod
   ```

### Backfilling Ingestion

**Scenario**: Missing historical data in bronze layer

**Steps**:
1. Identify date range to backfill
2. Run ingestion script for each date:
   ```bash
   for date in $(seq start_date end_date); do
       python ingestion/scripts/ingest_orders.py \
           --start-date $date \
           --end-date $date
   done
   ```

3. Validate data loaded correctly
4. Trigger transformation DAG or run dbt manually

## Deploying Changes

### Development to QA

1. **Create feature branch**:
   ```bash
   git checkout -b feature/new-model
   ```

2. **Make changes and test locally**:
   ```bash
   dbt run --target dev
   dbt test --target dev
   ```

3. **Create PR**:
   - Push to GitHub
   - Create pull request to `develop` branch
   - CI/CD runs automatically

4. **Review and merge**:
   - Code review
   - CI/CD passes
   - Merge to `develop`
   - Auto-deploys to QA environment

### QA to Production

1. **Validate in QA**:
   - Run full pipeline in QA
   - Validate data quality
   - Get stakeholder approval

2. **Merge to main**:
   ```bash
   git checkout main
   git merge develop
   git push origin main
   ```

3. **Production deployment**:
   - CI/CD automatically deploys to prod
   - Monitor Airflow DAG execution
   - Validate production data

4. **Rollback procedure** (if needed):
   ```bash
   # Revert git commit
   git revert <commit_hash>
   git push origin main
   
   # Or restore previous dbt models
   git checkout <previous_commit> -- dbt_project/models/
   ```

## Monitoring and Alerts

### Key Metrics to Monitor

1. **Ingestion**:
   - File counts in bronze layer
   - File sizes
   - Ingestion latency

2. **Transformation**:
   - dbt run success rate
   - Model execution time
   - Test pass rate

3. **Data Quality**:
   - Test failures
   - Row count changes
   - Data freshness

4. **Warehouse**:
   - Query performance
   - Storage costs
   - Compute usage

### Setting Up Alerts

1. **Airflow alerts**:
   - Configure email/Slack notifications in Airflow
   - Set up on DAG failure

2. **dbt alerts**:
   - Use dbt Cloud or custom monitoring
   - Alert on test failures

3. **Data quality alerts**:
   - Set up anomaly detection
   - Alert on significant data changes

## Troubleshooting

### dbt Models Not Updating

**Check**:
1. Is model materialized correctly?
   ```bash
   dbt run --select <model> --target dev
   ```

2. Are dependencies met?
   ```bash
   dbt list --select <model>+ --target dev
   ```

3. Check warehouse permissions

### Airflow DAG Not Running

**Check**:
1. DAG is enabled in Airflow UI
2. Schedule is correct
3. Dependencies are met
4. Airflow scheduler is running

### Data Quality Issues

**Investigation**:
1. Compare row counts:
   ```sql
   SELECT COUNT(*) FROM staging.stg_orders;
   SELECT COUNT(*) FROM raw_data.orders;
   ```

2. Check for nulls:
   ```sql
   SELECT COUNT(*) FROM staging.stg_orders WHERE order_id IS NULL;
   ```

3. Validate business rules:
   ```bash
   dbt test --select <model> --target dev
   ```

### Performance Issues

**Optimization**:
1. Check model materialization (table vs view)
2. Add indexes/clustering keys
3. Use incremental models for large tables
4. Partition large tables by date
5. Review query execution plans

## Emergency Procedures

### Production Incident

1. **Immediate actions**:
   - Stop affected DAGs in Airflow
   - Assess impact
   - Notify stakeholders

2. **Investigation**:
   - Check logs
   - Identify root cause
   - Determine fix

3. **Resolution**:
   - Apply fix
   - Test in dev/QA
   - Deploy to production
   - Monitor closely

4. **Post-incident**:
   - Document incident
   - Root cause analysis
   - Update runbook
   - Implement preventive measures


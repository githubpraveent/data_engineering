# Failure Recovery Runbook

## Dataflow Job Failures

### Streaming Job Failure

**Symptoms:**
- Job status shows "Failed" in Cloud Console
- No new data appearing in BigQuery
- Pub/Sub subscription backlog increasing

**Recovery Steps:**

1. **Identify the failure:**
   ```bash
   gcloud dataflow jobs describe JOB_ID --region=us-central1
   ```

2. **Check logs:**
   ```bash
   gcloud logging read "resource.type=dataflow_job AND resource.labels.job_id=JOB_ID" \
     --limit 50 --format json
   ```

3. **Common causes and fixes:**
   - **Schema mismatch**: Update BigQuery table schema
   - **Permission issues**: Check service account permissions
   - **Resource exhaustion**: Increase worker count or machine type
   - **Invalid data**: Check dead letter queue, fix data source

4. **Restart the job:**
   ```bash
   gcloud dataflow jobs run NEW_JOB_NAME \
     --gcs-location=gs://BUCKET/templates/streaming_pipeline_template \
     --region=us-central1 \
     --parameters=...
   ```

5. **Handle backlog:**
   - Job will automatically process backlogged messages
   - Monitor Pub/Sub subscription metrics

### Batch Job Failure

**Symptoms:**
- Job status shows "Failed"
- Data not appearing in target tables
- Airflow task failure

**Recovery Steps:**

1. **Identify the failure:**
   - Check Airflow task logs
   - Check Dataflow job logs

2. **Fix the issue:**
   - Correct data format issues
   - Fix schema mismatches
   - Resolve permission problems

3. **Rerun the job:**
   - Clear failed Airflow task
   - Or manually trigger Dataflow job

4. **Handle partial data:**
   - Check if any data was loaded
   - Decide if reprocessing is needed

## Airflow DAG Failures

### DAG Not Running

**Symptoms:**
- DAG shows as "Paused" or not scheduled
- No task instances created

**Recovery Steps:**

1. **Check DAG status:**
   - Log into Airflow UI
   - Verify DAG is unpaused
   - Check schedule_interval

2. **Check dependencies:**
   - Verify upstream DAGs completed
   - Check sensor conditions

3. **Manual trigger:**
   - Trigger DAG manually if needed
   - Clear blocking tasks

### Task Failures

**Symptoms:**
- Red task in Airflow UI
- Error messages in task logs

**Recovery Steps:**

1. **Review task logs:**
   - Click on failed task in Airflow UI
   - Review logs for error details

2. **Common issues:**
   - **BigQuery errors**: Check SQL syntax, permissions
   - **Dataflow errors**: See Dataflow failure recovery
   - **GCS errors**: Check bucket permissions, file existence
   - **Timeout errors**: Increase timeout or optimize query

3. **Fix and rerun:**
   - Fix the underlying issue
   - Clear the failed task
   - Task will automatically rerun

## BigQuery Issues

### Query Failures

**Symptoms:**
- Query returns error
- Timeout errors
- Resource exceeded errors

**Recovery Steps:**

1. **Check query syntax:**
   ```sql
   -- Validate query
   bq query --dry_run --use_legacy_sql=false "SELECT ..."
   ```

2. **Optimize query:**
   - Add WHERE clauses for partitioning
   - Use clustering columns
   - Limit result set size

3. **Increase resources:**
   - Purchase more slots
   - Use reservation for consistent workloads

### Data Quality Failures

**Symptoms:**
- Data quality DAG fails
- Validation checks fail

**Recovery Steps:**

1. **Identify failing checks:**
   - Review data quality DAG logs
   - Check which validations failed

2. **Investigate data issues:**
   - Query failing records
   - Identify root cause

3. **Fix data:**
   - Correct source data if possible
   - Update transformation logic
   - Manually fix data in BigQuery (last resort)

4. **Rerun checks:**
   - Clear failed data quality tasks
   - Verify fixes

## GCS Issues

### Bucket Access Issues

**Symptoms:**
- Permission denied errors
- Files not accessible

**Recovery Steps:**

1. **Check IAM permissions:**
   ```bash
   gsutil iam get gs://BUCKET_NAME
   ```

2. **Fix permissions:**
   ```bash
   gsutil iam ch serviceAccount:SERVICE_ACCOUNT:objectAdmin gs://BUCKET_NAME
   ```

### File Not Found

**Symptoms:**
- Pipeline fails with file not found
- Expected files missing

**Recovery Steps:**

1. **Verify file existence:**
   ```bash
   gsutil ls gs://BUCKET_NAME/path/to/file
   ```

2. **Check source system:**
   - Verify source system exported file
   - Check for delays in file arrival

3. **Handle missing data:**
   - Wait for file if delayed
   - Skip if file truly missing (with approval)
   - Reprocess when file arrives

## Pub/Sub Issues

### Message Backlog

**Symptoms:**
- High unacked message count
- Increasing backlog

**Recovery Steps:**

1. **Check subscription metrics:**
   ```bash
   gcloud pubsub subscriptions describe SUBSCRIPTION_NAME
   ```

2. **Scale Dataflow job:**
   - Increase worker count
   - Use larger machines

3. **Check for processing errors:**
   - Review Dataflow job logs
   - Fix processing issues

### Dead Letter Queue

**Symptoms:**
- Messages in dead letter queue
- Processing errors

**Recovery Steps:**

1. **Review dead letter messages:**
   ```bash
   gcloud pubsub subscriptions pull SUBSCRIPTION_NAME --limit=10
   ```

2. **Identify error patterns:**
   - Common schema issues
   - Invalid data formats

3. **Fix and reprocess:**
   - Fix source data if possible
   - Update pipeline to handle edge cases
   - Republish messages if needed

## Data Corruption

### Symptoms

- Data quality checks fail
- Unexpected data values
- Referential integrity violations

### Recovery Steps

1. **Identify affected data:**
   - Query for corrupted records
   - Determine date range affected

2. **Isolate corrupted data:**
   - Mark records as invalid
   - Move to quarantine table

3. **Reprocess data:**
   - Re-run pipeline for affected date range
   - Verify data quality

4. **Prevent recurrence:**
   - Add validation rules
   - Improve error handling

## Rollback Procedures

### Infrastructure Rollback

1. **Terraform rollback:**
   ```bash
   cd terraform/environments/ENV
   terraform state list
   terraform destroy -target=RESOURCE
   # Revert to previous commit
   git checkout PREVIOUS_COMMIT
   terraform apply
   ```

2. **Manual resource deletion:**
   - Delete resources via Cloud Console
   - Recreate with correct configuration

### Data Rollback

1. **BigQuery:**
   - Use point-in-time recovery (7 days)
   - Or restore from backup export

2. **GCS:**
   - Use versioning to restore previous version
   - Or restore from backup

3. **Reprocess:**
   - Re-run pipelines for affected date range
   - Verify data correctness

## Emergency Contacts

- **Data Engineering Team**: [Contact Info]
- **DevOps Team**: [Contact Info]
- **GCP Support**: [Support Plan Details]
- **On-Call Engineer**: [Rotation Schedule]

## Escalation Procedures

1. **Level 1**: Data Engineering Team
2. **Level 2**: DevOps + Data Engineering
3. **Level 3**: GCP Support + Management
4. **Level 4**: Executive escalation


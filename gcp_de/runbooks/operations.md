# Operations Runbook

## Daily Operations

### Morning Checklist

1. **Check Airflow DAG Status**
   - Log into Cloud Composer Airflow UI
   - Verify all DAGs from previous day completed successfully
   - Check for any failed tasks

2. **Monitor Dataflow Jobs**
   - Check Cloud Console → Dataflow → Jobs
   - Verify streaming jobs are running
   - Check for any failed batch jobs

3. **Review Data Quality Reports**
   - Check BigQuery for data quality check results
   - Review any alerts from Cloud Monitoring

4. **Check BigQuery Quota Usage**
   - Monitor slot usage
   - Check query performance

### Weekly Tasks

1. **Review Data Lake Storage**
   - Check GCS bucket sizes
   - Verify lifecycle policies are working
   - Review costs

2. **Performance Tuning**
   - Review slow BigQuery queries
   - Optimize Dataflow job configurations
   - Check for partition pruning opportunities

3. **Capacity Planning**
   - Review data growth trends
   - Plan for scaling if needed

## Monitoring and Alerting

### Key Metrics to Monitor

1. **Dataflow Jobs**
   - Job status (running/failed)
   - Processing latency
   - Throughput (records per second)
   - Worker utilization

2. **Airflow DAGs**
   - DAG success rate
   - Task duration
   - Failed task count

3. **BigQuery**
   - Query performance
   - Slot usage
   - Storage costs
   - Query errors

4. **GCS**
   - Bucket sizes
   - Object counts
   - Lifecycle policy execution

5. **Pub/Sub**
   - Message backlog
   - Publish/subscribe latency
   - Dead letter queue size

### Alerting Rules

Configure alerts for:
- Dataflow job failures
- Airflow DAG failures
- Data quality check failures
- High latency (> 1 hour for batch, > 5 min for streaming)
- BigQuery quota exceeded
- GCS bucket near capacity

## Common Operations

### Restart a Failed Dataflow Job

```bash
# List recent jobs
gcloud dataflow jobs list --region=us-central1 --status=JOB_STATE_FAILED

# View job details
gcloud dataflow jobs describe JOB_ID --region=us-central1

# Restart using template
gcloud dataflow jobs run JOB_NAME \
  --gcs-location=gs://BUCKET/templates/template_name \
  --region=us-central1 \
  --parameters=...
```

### Rerun a Failed Airflow DAG

1. Log into Airflow UI
2. Navigate to the failed DAG
3. Click "Clear" on failed tasks
4. Tasks will automatically rerun

### Check Data Quality

```bash
# Run data quality DAG manually
gcloud composer environments run ENV_NAME \
  --location us-central1 \
  dags trigger data_quality_checks
```

### Query BigQuery for Recent Data

```sql
-- Check recent transactions
SELECT COUNT(*) as count, MAX(load_timestamp) as latest_load
FROM `project.curated_dev.sales_fact`
WHERE DATE(transaction_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY);
```

## Scaling Operations

### Scale Dataflow Jobs

1. **Horizontal Scaling**: Increase `maxNumWorkers` in pipeline options
2. **Vertical Scaling**: Use larger machine types
3. **Auto-scaling**: Enable autoscaling in Dataflow options

### Scale Cloud Composer

1. Increase node count in Composer environment
2. Use larger machine types
3. Enable autoscaling (if available)

### Scale BigQuery

1. Purchase reserved slots for consistent workloads
2. Use query optimization (partitioning, clustering)
3. Consider materialized views for common queries

## Backup and Recovery

### BigQuery Backups

- Point-in-time recovery: 7 days automatic
- Export to GCS for longer retention:
  ```bash
  bq extract --destination_format=AVRO \
    project:dataset.table \
    gs://bucket/backup/table_*.avro
  ```

### GCS Backups

- Versioning enabled on critical buckets
- Lifecycle policies for archival
- Cross-region replication (if needed)

### Terraform State

- Stored in GCS with versioning
- Regular backups recommended

## Cost Optimization

### BigQuery

- Use partitioning and clustering
- Delete unused tables
- Use query result caching
- Optimize query patterns

### Dataflow

- Right-size worker machines
- Use preemptible workers for batch jobs
- Optimize windowing strategies

### GCS

- Use appropriate storage classes
- Implement lifecycle policies
- Delete old/unused data

### Cloud Composer

- Right-size environment
- Use appropriate machine types
- Monitor and optimize DAG execution


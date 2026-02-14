# Data Onboarding Guide

This guide describes the process for onboarding a new data source into the data lake and data warehouse.

## Prerequisites

- Access to source system
- Data schema documentation
- Sample data files
- Business requirements for the data

## Step-by-Step Process

### 1. Requirements Gathering

**Document:**
- Source system details (database, API, files)
- Data format (JSON, CSV, Parquet, etc.)
- Update frequency (real-time, hourly, daily, etc.)
- Data volume (records per day)
- Schema definition
- Business use cases

**Deliverables:**
- Data source specification document
- Schema definition
- Sample data files

### 2. Schema Design

**Create:**
- Staging table schema in BigQuery
- Curated table schema (if needed)
- Dimension/fact table design (if applicable)

**Considerations:**
- Data types
- Partitioning strategy
- Clustering columns
- Required vs optional fields

**Files to create:**
- `bigquery/schemas/create_staging_tables.sql` (add new table)
- `bigquery/schemas/create_curated_tables.sql` (if needed)

### 3. Infrastructure Setup

#### 3.1 Pub/Sub (for streaming sources)

```bash
# Create topic
gcloud pubsub topics create NEW_TOPIC_NAME --project=PROJECT_ID

# Create subscription for Dataflow
gcloud pubsub subscriptions create NEW_SUBSCRIPTION_NAME \
  --topic=NEW_TOPIC_NAME \
  --project=PROJECT_ID
```

**Update Terraform:**
- Add topic to `terraform/modules/pubsub/main.tf`
- Add subscription configuration

#### 3.2 GCS Buckets (for batch sources)

Buckets are already created, but verify:
- Landing bucket: `{project}-data-lake-raw-{env}`
- Staging bucket: `{project}-data-lake-staging-{env}`
- Curated bucket: `{project}-data-lake-curated-{env}`

**Create folder structure:**
```bash
gsutil mkdir gs://BUCKET/source_name/
```

#### 3.3 BigQuery Tables

Run schema creation scripts:
```bash
bq query --use_legacy_sql=false < bigquery/schemas/create_staging_tables.sql
```

### 4. Pipeline Development

#### 4.1 Streaming Pipeline (if applicable)

**Create or modify:**
- `dataflow/streaming/pubsub_to_gcs_bigquery.py`
- Add source-specific transformations
- Update schema mappings

**Deploy template:**
```bash
python dataflow/streaming/pubsub_to_gcs_bigquery.py \
  --runner DataflowRunner \
  --template_location gs://BUCKET/templates/NEW_TEMPLATE \
  --input_subscription projects/PROJECT/subscriptions/SUBSCRIPTION \
  --output_gcs gs://BUCKET/raw/source_name/ \
  --output_table PROJECT:staging_env.table_name
```

#### 4.2 Batch Pipeline (if applicable)

**Create or modify:**
- `dataflow/batch/gcs_transform_pipeline.py`
- Add source-specific transformations
- Update schema mappings

**Deploy template:**
```bash
python dataflow/batch/gcs_transform_pipeline.py \
  --runner DataflowRunner \
  --template_location gs://BUCKET/templates/NEW_TEMPLATE \
  --input gs://BUCKET/raw/source_name/ \
  --output_gcs gs://BUCKET/staging/source_name/ \
  --output_table PROJECT:staging_env.table_name \
  --input_format json
```

### 5. Airflow DAG Creation

**Create DAG:**
- `airflow/dags/NEW_SOURCE_DAG.py`
- Define tasks:
  - File detection (for batch)
  - Dataflow job execution
  - Data quality checks
  - Loading to curated tables

**Example structure:**
```python
with DAG(
    'new_source_etl',
    schedule_interval='0 2 * * *',
    ...
) as dag:
    check_files = GCSObjectsWithPrefixExistenceSensor(...)
    transform = DataflowTemplatedJobStartOperator(...)
    validate = BigQueryCheckOperator(...)
    load = BigQueryInsertJobOperator(...)
```

### 6. Data Quality Checks

**Add checks:**
- `airflow/dags/data_quality_dag.py` (add new checks)
- Or create source-specific quality DAG

**Checks to include:**
- Null primary keys
- Data freshness
- Row count validation
- Schema validation
- Business rule validation

### 7. Testing

#### 7.1 Unit Tests

Add tests to `tests/unit/test_dataflow_pipelines.py`:
- Test transformations
- Test validations
- Test error handling

#### 7.2 Integration Tests

Add tests to `tests/integration/test_pipeline_integration.py`:
- Test end-to-end flow
- Test data quality
- Test error scenarios

#### 7.3 Data Quality Tests

Add tests to `tests/data_quality/test_data_quality.py`:
- Source-specific validations
- Business rule checks

### 8. Documentation

**Update:**
- `README.md`: Add new source to architecture
- `architecture.md`: Document data flow
- Data Catalog: Add metadata
- This guide: Document any special considerations

### 9. Deployment

#### 9.1 Development Environment

1. Deploy infrastructure (Terraform)
2. Deploy pipelines (Dataflow templates)
3. Deploy DAGs (Airflow)
4. Test with sample data

#### 9.2 QA Environment

1. Promote code to QA branch
2. Deploy to QA environment
3. Run integration tests
4. Validate with production-like data

#### 9.3 Production Environment

1. Get approval for production deployment
2. Deploy to production
3. Monitor initial runs
4. Verify data quality

### 10. Monitoring Setup

**Configure:**
- Cloud Monitoring alerts
- Data quality dashboards
- Cost monitoring
- Performance metrics

**Alerts to set:**
- Pipeline failures
- Data quality failures
- High latency
- Resource exhaustion

## Checklist

- [ ] Requirements documented
- [ ] Schema designed and created
- [ ] Infrastructure provisioned (Pub/Sub, GCS, BigQuery)
- [ ] Pipeline developed and tested
- [ ] Airflow DAG created
- [ ] Data quality checks implemented
- [ ] Unit tests written
- [ ] Integration tests written
- [ ] Documentation updated
- [ ] Deployed to dev
- [ ] Deployed to QA
- [ ] Deployed to production
- [ ] Monitoring configured
- [ ] Runbook updated

## Common Patterns

### Pattern 1: Database CDC to Pub/Sub

1. Set up database change capture (Debezium, etc.)
2. Publish changes to Pub/Sub
3. Use streaming Dataflow pipeline
4. Load to BigQuery

### Pattern 2: File Dumps to GCS

1. Export files from source system
2. Upload to GCS landing bucket
3. Use batch Dataflow pipeline
4. Load to BigQuery

### Pattern 3: API to Pub/Sub

1. Create API connector
2. Publish to Pub/Sub
3. Use streaming Dataflow pipeline
4. Load to BigQuery

## Troubleshooting

### Common Issues

1. **Schema Mismatch**
   - Verify schema in BigQuery matches pipeline output
   - Check data type compatibility

2. **Permission Errors**
   - Verify service account permissions
   - Check IAM roles

3. **Data Quality Failures**
   - Review validation rules
   - Check source data quality
   - Adjust transformations if needed

4. **Performance Issues**
   - Optimize BigQuery queries
   - Adjust Dataflow worker configuration
   - Review partitioning strategy

## Support

For questions or issues during onboarding:
- Contact Data Engineering Team
- Review existing pipeline code
- Check documentation
- Consult runbooks


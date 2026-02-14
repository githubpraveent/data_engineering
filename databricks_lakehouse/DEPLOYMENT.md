# Deployment Guide

This guide provides step-by-step instructions for deploying the Databricks Lakehouse project.

## Prerequisites

1. **Databricks Workspace**
   - Unity Catalog enabled
   - Admin access to create catalogs, schemas, and tables
   - API token for automation

2. **Cloud Storage**
   - S3 bucket (AWS) or ADLS container (Azure) or GCS bucket (GCP)
   - Proper IAM roles/permissions for Databricks to access storage

3. **Streaming Source**
   - Kafka cluster, Azure Event Hubs, or AWS Kinesis
   - Connection credentials and topic/stream names

4. **Development Tools**
   - Databricks CLI installed and configured
   - Terraform (for infrastructure deployment)
   - Python 3.8+ (for local development)

## Step 1: Infrastructure Setup

### 1.1 Configure Cloud Storage

**AWS S3:**
```bash
# Create S3 bucket
aws s3 mb s3://databricks-lakehouse

# Create folders
aws s3 mkdir s3://databricks-lakehouse/data/
aws s3 mkdir s3://databricks-lakehouse/checkpoints/
```

**Azure ADLS:**
```bash
# Create storage account and container
az storage account create --name databrickslakehouse --resource-group rg-databricks
az storage container create --name data --account-name databrickslakehouse
az storage container create --name checkpoints --account-name databrickslakehouse
```

### 1.2 Deploy Infrastructure with Terraform

```bash
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Set variables
export TF_VAR_databricks_workspace_url="https://<workspace>.cloud.databricks.com"
export TF_VAR_databricks_token="<your-token>"
export TF_VAR_s3_bucket_name="databricks-lakehouse"

# Plan deployment
terraform plan

# Apply
terraform apply
```

## Step 2: Unity Catalog Setup

### 2.1 Create Catalogs and Schemas

Run the Unity Catalog setup script:

```bash
# Using Databricks CLI
databricks workspace import config/unity_catalog_config.sql /Shared/lakehouse/setup/

# Or execute directly in Databricks SQL
# Copy contents of config/unity_catalog_config.sql and run in SQL editor
```

### 2.2 Configure Storage Credentials

**AWS:**
```sql
CREATE STORAGE CREDENTIAL aws_credential
WITH (
  TYPE = AWS_IAM_ROLE,
  ROLE_ARN = 'arn:aws:iam::<account-id>:role/databricks-lakehouse-role'
);
```

**Azure:**
```sql
CREATE STORAGE CREDENTIAL azure_credential
WITH (
  TYPE = AZURE_SAS_TOKEN,
  AZURE_SAS_TOKEN = '<sas-token>'
);
```

## Step 3: Import Notebooks

### 3.1 Upload Notebooks to Workspace

```bash
# Import all notebooks
databricks workspace import_dir notebooks/ /Shared/lakehouse/notebooks/

# Import workflows
databricks workspace import workflows/dlt_pipeline.py /Shared/lakehouse/workflows/
```

### 3.2 Upload Configuration Files

```bash
# Upload config files
databricks fs cp config/ dbfs:/Shared/lakehouse/config/ --recursive
```

## Step 4: Configure Secrets

### 4.1 Create Secret Scopes

```bash
# Create scope for Kafka credentials
databricks secrets create-scope kafka

# Add secrets
databricks secrets put --scope kafka --key bootstrap_servers
databricks secrets put --scope kafka --key username
databricks secrets put --scope kafka --key password
```

### 4.2 Create Databricks API Token Secret

```bash
databricks secrets create-scope databricks
databricks secrets put --scope databricks --key api_token
```

## Step 5: Deploy Streaming Pipeline

### 5.1 Option A: Delta Live Tables (Recommended)

1. Go to Databricks UI → Workflows → Delta Live Tables
2. Create new pipeline
3. Set source path: `/Shared/lakehouse/workflows/dlt_pipeline.py`
4. Configure:
   - Target: `lakehouse`
   - Storage location: `s3://databricks-lakehouse/data/`
   - Checkpoint location: `s3://databricks-lakehouse/checkpoints/`
5. Start pipeline

### 5.2 Option B: Databricks Jobs

```bash
# Create job from workflow definition
databricks jobs create --json-file workflows/workflow_definition.json
```

Or use UI:
1. Go to Databricks UI → Workflows → Jobs
2. Create new job
3. Add tasks for each notebook in order:
   - `01_bronze_ingestion`
   - `02_silver_transformation`
   - `03_gold_aggregation`
   - `05_ml_inference`
   - `07_monitoring`
4. Configure schedule (e.g., every 15 minutes)
5. Set cluster configuration
6. Save and run

## Step 6: ML Model Training

### 6.1 Initial Model Training

1. Open notebook `04_ml_training.py`
2. Run all cells
3. Model will be registered in MLflow
4. Promote to Production stage after validation

### 6.2 Set Up Model Serving (Optional)

```python
# In Databricks UI or via API
# Create serving endpoint for real-time inference
```

Or use `ai_query` function directly in notebooks (simpler).

## Step 7: Configure Monitoring

### 7.1 Set Up Monitoring Dashboard

1. Create new Databricks SQL dashboard
2. Add queries from `08_bi_queries.py`
3. Set refresh interval
4. Configure alerts on key metrics

### 7.2 Schedule Monitoring Job

```bash
# Create monitoring job
databricks jobs create \
  --name "lakehouse-monitoring" \
  --notebook-path "/Shared/lakehouse/notebooks/07_monitoring" \
  --schedule-cron "0 */15 * * * ?" \
  --max-retries 1
```

## Step 8: Access Control Setup

### 8.1 Assign Users to Roles

```sql
-- Assign users to roles
GRANT ROLE data_engineers TO USER `engineer@company.com`;
GRANT ROLE data_analysts TO USER `analyst@company.com`;
GRANT ROLE ml_engineers TO USER `ml@company.com`;
GRANT ROLE business_users TO USER `business@company.com`;
```

### 8.2 Verify Permissions

```sql
-- Check grants
SHOW GRANTS ON CATALOG lakehouse;
SHOW GRANTS ON SCHEMA silver;
SHOW GRANTS ON TABLE gold.customer_behavior_daily;
```

## Step 9: Testing

### 9.1 Run Unit Tests

```bash
# Install pytest
pip install pytest pyspark delta-spark

# Run tests
pytest tests/ -v
```

### 9.2 Validate Pipeline

1. Check Bronze table has data:
   ```sql
   SELECT COUNT(*) FROM lakehouse.bronze.customer_events_raw;
   ```

2. Check Silver transformations:
   ```sql
   SELECT COUNT(*) FROM lakehouse.silver.customer_events_cleaned;
   SELECT AVG(quality_score) FROM lakehouse.silver.customer_events_cleaned;
   ```

3. Check Gold aggregations:
   ```sql
   SELECT COUNT(*) FROM lakehouse.gold.customer_behavior_daily;
   ```

## Step 10: Performance Optimization

### 10.1 Apply Spark Optimizations

Run the performance optimization notebook:

```bash
# Import optimization notebook
databricks workspace import notebooks/09_performance_optimization.py /Shared/lakehouse/notebooks/
```

### 10.2 Schedule Optimization Jobs

```bash
# Create optimization workflow
databricks jobs create --json-file workflows/optimization_schedule.json
```

Or manually:
1. Go to Databricks UI → Workflows → Jobs
2. Create new job from `09_performance_optimization.py`
3. Schedule daily at 2 AM (low traffic time)
4. Configure cluster with optimization settings

### 10.3 Enable Auto-Optimize

Auto-optimize is already enabled in cluster configurations, but verify:

```python
# In any notebook
spark.conf.get("spark.databricks.delta.optimizeWrite.enabled")
# Should return 'true'
```

### 10.4 Initial Optimization Run

Run optimization manually first:

```python
# In Databricks notebook
from utils.performance_optimizer import DeltaTableOptimizer, SparkConfigOptimizer

# Apply Spark optimizations
spark_opt = SparkConfigOptimizer(spark)
spark_opt.apply_all_optimizations()

# Optimize tables
delta_opt = DeltaTableOptimizer(spark)
delta_opt.optimize_table("lakehouse.silver.customer_events_cleaned", 
                         z_order_cols=["customer_id", "event_date"])
```

## Step 11: Production Checklist

- [ ] All secrets configured
- [ ] Unity Catalog catalogs and schemas created
- [ ] Storage credentials configured
- [ ] Streaming pipeline running
- [ ] ML model trained and registered
- [ ] Monitoring dashboard created
- [ ] Alerts configured
- [ ] Access control set up
- [ ] Documentation updated
- [ ] Backup and recovery plan in place

## Troubleshooting

### Streaming Not Processing

1. Check checkpoint location permissions
2. Verify Kafka/Event Hubs connectivity
3. Check streaming query status:
   ```python
   streams = spark.streams.active
   for stream in streams:
       print(stream.lastProgress)
   ```

### Data Quality Issues

1. Review data quality metrics:
   ```sql
   SELECT * FROM lakehouse.monitoring.data_quality_metrics
   ORDER BY event_date DESC;
   ```

2. Check for schema mismatches
3. Review transformation logic in Silver notebook

### ML Model Issues

1. Check model registry:
   ```python
   from mlflow.tracking import MlflowClient
   client = MlflowClient()
   client.get_latest_versions("customer_sentiment_classifier")
   ```

2. Verify training data quality
3. Check inference pipeline logs

## Maintenance

### Regular Tasks

1. **Daily**: 
   - Review monitoring dashboard
   - Check optimization job status
2. **Weekly**: 
   - Review data quality metrics
   - Verify optimization schedules are running
3. **Monthly**: 
   - Retrain ML model with new data
   - Review and adjust optimization strategies
   - Analyze query performance trends
4. **Quarterly**: 
   - Review and optimize Delta tables (VACUUM, OPTIMIZE)
   - Update Z-ordering strategies based on query patterns
   - Review and adjust Spark configurations

### Delta Table Maintenance

```sql
-- Optimize tables with Z-ordering
OPTIMIZE lakehouse.silver.customer_events_cleaned
ZORDER BY (customer_id, event_date, event_type);

-- Optimize Gold tables
OPTIMIZE lakehouse.gold.customer_behavior_daily
ZORDER BY (customer_id, event_date);

-- Vacuum old files (retention)
VACUUM lakehouse.bronze.customer_events_raw RETAIN 90 HOURS;

-- Create bloom filters for fast lookups
CREATE BLOOM FILTER INDEX
ON TABLE lakehouse.silver.customer_events_cleaned
FOR COLUMNS(customer_id OPTIONS (fpp=0.1, numItems=10000000));
```

### Performance Monitoring

```sql
-- Check table statistics
DESCRIBE DETAIL lakehouse.silver.customer_events_cleaned;

-- View optimization history
DESCRIBE HISTORY lakehouse.silver.customer_events_cleaned
WHERE operation = 'OPTIMIZE'
ORDER BY timestamp DESC;
```

## Support

For issues or questions:
1. Check logs in Databricks UI
2. Review monitoring alerts
3. Consult architecture documentation
4. Contact data engineering team

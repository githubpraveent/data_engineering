# Onboarding Guide: Adding a New Retail Source

This guide walks through the process of onboarding a new retail data source (e.g., a new POS system, rewards database, or inventory system) into the data lake and warehouse.

## Overview

When adding a new source, you need to:
1. Define the source schema and data format
2. Set up ingestion infrastructure (Event Hubs or ADF)
3. Create Databricks ingestion jobs
4. Build transformation pipelines
5. Map to data warehouse dimensions/facts
6. Create Airflow DAGs
7. Set up data quality checks

## Step-by-Step Process

### Step 1: Define Source Schema

#### Document Source Characteristics
- **Source Type**: Real-time (Event Hubs) or Batch (ADF)
- **Data Format**: JSON, CSV, Parquet, Database table
- **Schema**: Document all fields, data types, constraints
- **Volume**: Expected data volume (records/day, size)
- **Frequency**: How often data is produced/updated

#### Example: New POS System
```yaml
source_name: pos_system_v2
source_type: real-time
data_format: json
schema:
  - field: transaction_id
    type: string
    required: true
  - field: store_id
    type: string
    required: true
  - field: items
    type: array
    required: true
volume: 100000 records/day
frequency: real-time (events)
```

### Step 2: Set Up Ingestion Infrastructure

#### For Real-Time Sources (Event Hubs)

1. **Create Event Hub**
   ```bash
   # Update Terraform: terraform/modules/event-hubs/main.tf
   resource "azurerm_eventhub" "new_source" {
     name                = "new-pos-events"
     namespace_name      = azurerm_eventhub_namespace.main.name
     resource_group_name = var.resource_group_name
     partition_count     = 4
     message_retention   = 7
   }
   ```

2. **Create Consumer Group**
   ```bash
   resource "azurerm_eventhub_consumer_group" "databricks_new_source" {
     name                = "databricks-streaming"
     namespace_name      = azurerm_eventhub_namespace.main.name
     eventhub_name       = azurerm_eventhub.new_source.name
     resource_group_name = var.resource_group_name
   }
   ```

3. **Deploy Infrastructure**
   ```bash
   cd terraform/environments/dev
   terraform plan
   terraform apply
   ```

#### For Batch Sources (ADF)

1. **Create ADF Linked Service**
   - Azure Portal → Data Factory → Linked Services
   - Configure connection to source database/file system

2. **Create ADF Dataset**
   - Define source dataset with schema
   - Configure file format and location

3. **Create ADF Pipeline**
   - Copy activity from source to ADLS Bronze
   - Configure schedule/trigger

### Step 3: Create Databricks Ingestion Notebook

#### For Streaming Sources

Create: `databricks/notebooks/ingestion/stream_new_source_to_bronze.py`

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # Stream New Source Events to Bronze

# Configuration
dbutils.widgets.text("event_hub_name", "new-pos-events")
dbutils.widgets.text("bronze_path", "")
dbutils.widgets.text("checkpoint_path", "")

# Event Hubs configuration
ehConf = {
    'eventhubs.connectionString': dbutils.secrets.get(scope="azure-key-vault", key="event-hubs-connection-string"),
    'eventhubs.consumerGroup': 'databricks-streaming',
    'eventhubs.startingPosition': 'latest'
}

# Define schema
schema = StructType([
    StructField("transaction_id", StringType(), True),
    StructField("store_id", StringType(), True),
    # Add all fields from source schema
])

# Stream and write to Bronze
df_stream = (
    spark
    .readStream
    .format("eventhubs")
    .options(**ehConf)
    .load()
)

# Parse and write to Delta
# ... (implementation)
```

#### For Batch Sources

Create: `databricks/notebooks/ingestion/batch_new_source_to_bronze.py`

```python
# Read from ADLS Bronze (loaded by ADF)
df = spark.read.format("delta").load(bronze_path)

# Apply transformations
# Write to Bronze in Delta format
df.write.format("delta").mode("append").save(bronze_path)
```

### Step 4: Create Transformation Notebooks

#### Bronze to Silver

Create: `databricks/notebooks/transformation/bronze_to_silver_new_source.py`

```python
# Read from Bronze
df_bronze = spark.read.format("delta").load(bronze_path)

# Apply cleaning and validation
df_cleaned = df_bronze.filter(
    col("transaction_id").isNotNull() &
    col("store_id").isNotNull()
)

# Standardize fields
df_standardized = df_cleaned.withColumn(
    "store_id", upper(trim(col("store_id")))
)

# Deduplicate
# ... (implementation)

# Write to Silver
df_standardized.write.format("delta").mode("overwrite").save(silver_path)
```

#### Silver to Gold

Create: `databricks/notebooks/transformation/silver_to_gold_new_source.py`

```python
# Read from Silver
df_silver = spark.read.format("delta").load(silver_path)

# Apply business logic
# Join with other sources if needed
# Create curated fact/dimension tables

# Write to Gold
df_gold.write.format("delta").mode("overwrite").save(gold_path)
```

### Step 5: Create Synapse Staging Table

Create: `synapse/schemas/staging_new_source.sql`

```sql
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[staging].[new_source_data]') AND type in (N'U'))
BEGIN
    CREATE TABLE [staging].[new_source_data] (
        [transaction_id] NVARCHAR(100) NOT NULL,
        [store_id] NVARCHAR(50) NOT NULL,
        -- Add all fields from source
        [ingestion_timestamp] DATETIME2 NOT NULL,
        [processing_date] DATE NOT NULL
    )
    WITH (
        DISTRIBUTION = HASH([transaction_id]),
        CLUSTERED COLUMNSTORE INDEX
    )
END
GO
```

### Step 6: Map to Data Warehouse

#### Dimension Mapping

Determine which dimensions this source contributes to:
- **Customer Dimension**: If source has customer data
- **Product Dimension**: If source has product data
- **Store Dimension**: If source has store data
- **New Dimension**: If source introduces new dimension

#### Fact Mapping

Determine which fact tables this source feeds:
- **Sales Fact**: If source has sales transactions
- **Order Fact**: If source has orders
- **New Fact**: If source introduces new fact

#### Update Stored Procedures

Update or create stored procedures:
- `sp_load_customer_dimension.sql` (if customer data)
- `sp_load_sales_fact.sql` (if sales data)
- Or create new procedures for new dimensions/facts

### Step 7: Create Airflow DAG

#### Ingestion DAG

Create: `airflow/dags/ingestion/ingest_new_source.py`

```python
from airflow import DAG
from airflow.providers.microsoft.azure.operators.databricks import DatabricksSubmitRunOperator

with DAG(
    'ingest_new_source',
    default_args=default_args,
    schedule_interval=timedelta(minutes=15),
    # ... configuration
) as dag:
    
    stream_to_bronze = DatabricksSubmitRunOperator(
        task_id='stream_new_source_to_bronze',
        # ... configuration
    )
```

#### Transformation DAG

Create: `airflow/dags/transformation/transform_new_source.py`

```python
with DAG(
    'transform_new_source',
    # ... configuration
) as dag:
    
    bronze_to_silver = DatabricksSubmitRunOperator(
        task_id='bronze_to_silver_new_source',
        # ... configuration
    )
    
    silver_to_gold = DatabricksSubmitRunOperator(
        task_id='silver_to_gold_new_source',
        # ... configuration
    )
```

### Step 8: Set Up Data Quality Checks

#### Create Quality Notebook

Create: `databricks/notebooks/quality/validate_new_source.py`

```python
# Schema validation
# Completeness checks
# Data type validation
# Business rule validation
```

#### Add to Airflow DAG

```python
quality_check = DatabricksSubmitRunOperator(
    task_id='quality_check_new_source',
    # ... configuration
)
```

### Step 9: Update Purview Data Catalog

1. **Register Source in Purview**
   - Azure Portal → Purview → Data Catalog
   - Add new source system
   - Scan ADLS containers for new source data

2. **Document Lineage**
   - Map source → Bronze → Silver → Gold → Warehouse
   - Document transformations and business rules

3. **Add Business Glossary Terms**
   - Define terms specific to new source
   - Link to data assets

### Step 10: Testing and Validation

#### Unit Tests
- Test schema parsing
- Test transformation logic
- Test SCD logic (if applicable)

#### Integration Tests
- End-to-end data flow test
- Verify data in Bronze → Silver → Gold
- Verify warehouse loads

#### Data Quality Tests
- Run quality checks
- Verify completeness, accuracy
- Check referential integrity

### Step 11: Deployment

1. **Deploy to Dev**
   ```bash
   # Deploy via CI/CD or manually
   git checkout dev
   git add .
   git commit -m "Add new source: new-pos-system"
   git push origin dev
   ```

2. **Test in Dev**
   - Run ingestion DAG
   - Verify data flow
   - Check quality metrics

3. **Deploy to QA**
   ```bash
   git checkout qa
   git merge dev
   git push origin qa
   ```

4. **Test in QA**
   - Full integration testing
   - Performance testing
   - User acceptance testing

5. **Deploy to Production**
   ```bash
   git checkout main
   git merge qa
   git push origin main
   ```

## Checklist

- [ ] Source schema documented
- [ ] Event Hub or ADF pipeline created
- [ ] Databricks ingestion notebook created
- [ ] Bronze to Silver transformation created
- [ ] Silver to Gold transformation created
- [ ] Synapse staging table created
- [ ] Dimension/fact mapping defined
- [ ] Stored procedures updated/created
- [ ] Airflow DAGs created
- [ ] Data quality checks implemented
- [ ] Purview catalog updated
- [ ] Tests written and passing
- [ ] Deployed to Dev and tested
- [ ] Deployed to QA and tested
- [ ] Deployed to Production
- [ ] Documentation updated

## Example: Onboarding a New Rewards Database

### Source Details
- **Type**: Batch (SQL Server database)
- **Frequency**: Daily export
- **Schema**: Customer rewards points, redemption history

### Steps Taken
1. Created ADF pipeline to extract from SQL Server
2. Created Databricks notebook to transform rewards data
3. Mapped to Customer dimension (for customer attributes)
4. Created new Rewards fact table
5. Created Airflow DAG for daily batch load
6. Added data quality checks
7. Updated Purview catalog

### Result
- Rewards data now flows: Source → Bronze → Silver → Gold → Warehouse
- Customer dimension enriched with rewards information
- New Rewards fact table available for analytics

## Support

For questions or issues during onboarding:
- **Data Engineering Team**: data-engineering@company.com
- **Documentation**: See architecture.md and runbook.md
- **Slack Channel**: #data-engineering


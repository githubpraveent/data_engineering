# Architecture Documentation

## System Architecture

### Data Flow

#### Streaming Pipeline
1. **Source**: Transactional database publishes CDC events to Pub/Sub
2. **Ingestion**: Dataflow streaming job consumes from Pub/Sub
3. **Landing**: Raw events written to GCS (raw zone) in real-time
4. **Transformation**: Dataflow applies basic transformations
5. **Loading**: Data written to BigQuery staging tables
6. **Orchestration**: Cloud Composer monitors and manages streaming jobs

#### Batch Pipeline
1. **Source**: External systems export files (CSV/JSON) to GCS landing bucket
2. **Detection**: Airflow sensor detects new files in GCS
3. **Transformation**: Dataflow batch job reads from GCS, transforms, writes to staging
4. **Validation**: Data quality checks run on staging data
5. **Loading**: Validated data loaded to curated zone and BigQuery
6. **Orchestration**: Cloud Composer DAG orchestrates entire batch flow

### Data Zones (Medallion Architecture)

#### Bronze (Raw Zone)
- **Location**: `gs://{project}-data-lake-raw/`
- **Purpose**: Store raw, unprocessed data exactly as received
- **Format**: JSON, CSV, Parquet
- **Retention**: 90 days (configurable)
- **Schema**: Schema-on-read, minimal validation

#### Silver (Staging Zone)
- **Location**: `gs://{project}-data-lake-staging/`
- **Purpose**: Cleaned, validated, and standardized data
- **Format**: Parquet (optimized for analytics)
- **Retention**: 180 days
- **Schema**: Enforced schema, data quality checks applied

#### Gold (Curated Zone)
- **Location**: `gs://{project}-data-lake-curated/` + BigQuery
- **Purpose**: Business-ready, aggregated, and modeled data
- **Format**: BigQuery tables, Parquet in GCS
- **Retention**: 7 years (compliance)
- **Schema**: Star schema (dimensions + facts), SCD applied

### Component Details

#### Cloud Pub/Sub
- **Topics**: 
  - `retail-transactions` (streaming transactions)
  - `retail-inventory` (inventory updates)
  - `retail-customers` (customer events)
- **Subscriptions**: One per Dataflow streaming job
- **Message Format**: JSON with schema versioning
- **Retention**: 7 days

#### Cloud Storage (GCS)
- **Bucket Naming**: `{project}-data-lake-{zone}-{env}`
- **Lifecycle Policies**: 
  - Raw: Delete after 90 days
  - Staging: Delete after 180 days
  - Curated: Archive to Coldline after 1 year, delete after 7 years
- **Partitioning**: Date-based partitioning (`year=YYYY/month=MM/day=DD`)

#### Dataflow
- **Streaming Jobs**:
  - Pub/Sub → GCS (raw)
  - Pub/Sub → BigQuery (staging)
  - Window: 5-minute fixed windows
  - Late data: 1-hour allowed lateness
- **Batch Jobs**:
  - GCS → GCS (transformations)
  - GCS → BigQuery (loads)
  - Autoscaling: 1-100 workers
  - Machine Type: n1-standard-4

#### BigQuery
- **Datasets**:
  - `staging_{env}`: Raw/lightly transformed data
  - `curated_{env}`: Clean, modeled data
  - `analytics_{env}`: Aggregated, reporting tables
- **Partitioning**: Date-based for fact tables
- **Clustering**: By business keys (customer_id, product_id, etc.)
- **Materialized Views**: For common aggregations

#### Cloud Composer (Airflow)
- **Environment**: Separate for dev/qa/prod
- **DAG Schedule**: 
  - Batch: Daily at 2 AM UTC
  - Streaming: Continuous (monitoring DAG)
  - SCD: Hourly for Type 2 dimensions
- **DAGs**:
  - `batch_etl_dag`: Full batch pipeline
  - `streaming_pipeline_dag`: Streaming job monitoring
  - `scd_dimension_dag`: Dimension updates (SCD Type 1/2)
  - `data_quality_dag`: Data validation checks

### Data Modeling

#### Dimension Tables
- **Customer Dimension** (SCD Type 2)
  - Tracks historical changes
  - Effective date / expiration date
  - Current flag
- **Product Dimension** (SCD Type 2)
  - Product attributes with history
- **Store Dimension** (SCD Type 1)
  - Current state only
- **Date Dimension**
  - Pre-populated calendar table

#### Fact Tables
- **Sales Fact**
  - Grain: One row per transaction line item
  - Partitioned by transaction_date
  - Clustered by customer_id, product_id
- **Inventory Fact**
  - Grain: Daily snapshot per product/store
  - Partitioned by snapshot_date
- **Customer Activity Fact**
  - Grain: One row per customer event
  - Partitioned by event_timestamp

### Security & Access Control

#### IAM Roles
- **Data Engineers**: Full access to Dataflow, Composer, BigQuery
- **Data Analysts**: Read-only access to curated datasets
- **Data Scientists**: Read access to staging + curated
- **DevOps**: Infrastructure management (Terraform)

#### Data Encryption
- **At Rest**: GCS and BigQuery default encryption
- **In Transit**: TLS 1.2+ for all connections
- **Key Management**: Cloud KMS for sensitive data

### Monitoring & Alerting

#### Cloud Monitoring Metrics
- Dataflow job status, latency, throughput
- BigQuery query performance, slot usage
- Composer DAG success/failure rates
- GCS bucket sizes, object counts

#### Cloud Logging
- Dataflow job logs
- Airflow task logs
- BigQuery audit logs
- Application logs

#### Alerting
- Dataflow job failures
- DAG failures
- Data quality check failures
- High latency (> 1 hour for batch, > 5 min for streaming)

### Scalability

#### Horizontal Scaling
- Dataflow: Auto-scaling based on backlog
- BigQuery: Automatic slot allocation
- Composer: Managed scaling by GCP

#### Performance Optimization
- BigQuery: Partitioning + clustering
- GCS: Lifecycle policies for cost optimization
- Dataflow: Appropriate windowing strategies

### Disaster Recovery

#### Backup Strategy
- BigQuery: Point-in-time recovery (7 days)
- GCS: Versioning enabled for critical buckets
- Terraform state: Stored in GCS with versioning

#### Recovery Procedures
- See [Failure Recovery Runbook](runbooks/failure_recovery.md)


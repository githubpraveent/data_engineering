# Architecture Documentation

## System Architecture

### Overview

This solution implements a modern data lake and data warehouse architecture on AWS, designed to handle streaming, batch, and CDC workloads from Azure SQL Server sources.

### Key Design Principles

1. **Medallion Architecture**: Data flows through landing → staging → curated zones
2. **Separation of Concerns**: Streaming and batch processing are separate pipelines
3. **Schema Evolution**: Support for schema changes via Kafka Schema Registry
4. **Environment Isolation**: Complete separation of dev/qa/prod environments
5. **Infrastructure as Code**: All infrastructure managed via Terraform
6. **CI/CD**: Automated deployment and testing via GitHub Actions

## Component Details

### 1. Ingestion Layer

#### Amazon MSK (Managed Streaming for Kafka)

- **Purpose**: Central event streaming platform
- **Configuration**:
  - Multi-AZ deployment for high availability
  - Encryption at rest and in transit
  - IAM authentication
  - Auto-scaling based on throughput

#### Kafka Topics

Topics are organized by source table and operation type:

- `retail.customer.cdc` - Customer table CDC events
- `retail.order.cdc` - Order table CDC events
- `retail.product.cdc` - Product table CDC events
- `retail.order_item.cdc` - Order items CDC events

Each topic uses:
- Avro schema for message format
- Retention: 7 days (configurable)
- Partitions: Based on expected throughput

#### Kafka Producers (Azure/On-Prem)

- Debezium CDC connector for SQL Server
- Publishes CDC events to MSK topics
- Handles schema registry integration
- Retry logic and error handling

### 2. Storage Layer

#### S3 Data Lake (Medallion Architecture)

**Landing Zone** (`s3://retail-datalake-{env}/landing/`)
- Raw CDC events from Kafka
- Partitioned by: `table_name/year/month/day/hour/`
- Format: Parquet (compressed)
- Retention: 90 days

**Staging Zone** (`s3://retail-datalake-{env}/staging/`)
- Cleaned and validated data
- Schema validation applied
- Data quality checks passed
- Partitioned similarly to landing

**Curated Zone** (`s3://retail-datalake-{env}/curated/`)
- Business-ready, transformed data
- Star schema dimensions and facts
- Optimized for analytics
- Long-term retention

#### Glue Data Catalog

- Centralized metadata repository
- Schema discovery via Glue Crawlers
- Data lineage tracking
- Integration with Athena, Redshift Spectrum

### 3. Processing Layer

#### AWS Glue Streaming Jobs

**Purpose**: Real-time ingestion from MSK to S3

**Features**:
- Consumes from MSK topics
- Applies basic transformations (schema validation, deduplication)
- Writes to S3 landing zone in Parquet format
- Handles late-arriving data
- Checkpointing for exactly-once processing

**Job Configuration**:
- Worker type: G.1X or G.2X
- Number of workers: Auto-scaling
- Spark streaming: Micro-batch (1 minute intervals)

#### AWS Glue Batch Jobs

**Purpose**: Transform data from landing → staging → curated

**Job Types**:
1. **Landing to Staging**: Data quality, validation, cleaning
2. **Staging to Curated**: Business logic, aggregations, star schema creation

**Features**:
- Spark-based transformations
- Error handling and dead letter queues
- Data quality metrics
- Incremental processing

### 4. Data Warehouse (Redshift)

#### Architecture

- **Cluster Type**: Redshift Serverless (or provisioned)
- **Node Type**: RA3 (for separation of compute and storage)
- **Networking**: Private subnets, VPC endpoints

#### Schema Design

**Staging Schema** (`staging`)
- Raw tables mirroring source structure
- Streaming ingestion tables (from MSK)
- Batch load staging tables (from S3)

**Analytics Schema** (`analytics`)
- Star schema design
- Dimensions: Customer, Product, Date, etc.
- Facts: Sales, Orders, etc.

#### Streaming Ingestion

- Materialized views consuming from MSK
- Auto-refresh every 1 minute
- Handles schema evolution
- Error handling and retries

#### SCD Processing

**Type 1 (Overwrite)**
- Direct updates to dimension tables
- No history maintained
- Used for: Product descriptions, customer addresses

**Type 2 (History)**
- Maintains full history with effective dates
- Surrogate keys
- Current flag for active records
- Used for: Customer demographics, product categories

### 5. Infrastructure Components

#### Networking

- VPC with public/private subnets
- MSK in private subnets
- Redshift in private subnets
- VPC endpoints for S3, Glue, etc.
- Security groups with least privilege

#### IAM Roles

- **Glue Service Role**: Access to S3, MSK, Glue Catalog
- **Redshift Role**: Access to S3 for COPY commands
- **MSK Access**: IAM-based authentication
- **Lambda Roles**: For any serverless components

#### Monitoring & Logging

- CloudWatch Logs for all services
- CloudWatch Metrics for:
  - MSK: Throughput, lag, errors
  - Glue: Job success/failure, duration
  - Redshift: Query performance, storage
- CloudWatch Alarms for critical failures

## Data Flow Examples

### Streaming Path (Real-time)

```
SQL Server CDC → Kafka Producer → MSK Topic
                                      ↓
                          ┌───────────┴───────────┐
                          │                       │
                    Glue Streaming          Redshift Streaming
                    (MSK → S3 Landing)     (MSK → Redshift MV)
                          │                       │
                          ↓                       ↓
                    S3 Landing Zone        Redshift Staging
```

### Batch Path (Scheduled)

```
S3 Landing Zone
      ↓
Glue Batch Job (Landing → Staging)
      ↓
S3 Staging Zone
      ↓
Glue Batch Job (Staging → Curated)
      ↓
S3 Curated Zone
      ↓
Redshift COPY (S3 → Redshift Staging)
      ↓
Redshift SCD/Fact Processing
      ↓
Redshift Analytics Schema
```

## Security

- **Encryption**: 
  - S3: Server-side encryption (SSE-S3 or SSE-KMS)
  - MSK: Encryption at rest and in transit
  - Redshift: Encryption at rest
- **Network**: Private subnets, VPC endpoints
- **Access Control**: IAM roles with least privilege
- **Data Governance**: Glue Data Catalog for access policies

## Scalability

- **MSK**: Auto-scaling based on throughput
- **Glue**: Auto-scaling workers
- **Redshift**: Concurrency scaling, elastic resize
- **S3**: Unlimited scale

## Disaster Recovery

- **Multi-AZ**: MSK and Redshift in multiple AZs
- **Backups**: 
  - Redshift automated snapshots
  - S3 versioning and cross-region replication (optional)
- **RTO/RPO**: Defined per environment

## Cost Optimization

- **Redshift Serverless**: Pay per query (for dev/qa)
- **S3 Lifecycle Policies**: Move old data to Glacier
- **Glue Job Optimization**: Right-sizing workers
- **MSK**: Right-sizing broker instances


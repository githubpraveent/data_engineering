# Retail Data Lakehouse Architecture

## Overview

This document describes the architecture of the retail data lakehouse built on Databricks, using Delta Lake, Unity Catalog, and Apache Airflow for orchestration.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA SOURCES                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   POS        │  │   Orders     │  │  Inventory   │  │   Kafka      │  │
│  │   Systems    │  │   Database   │  │  Database    │  │   Events     │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                  │                  │                  │           │
└─────────┼──────────────────┼──────────────────┼──────────────────┼───────────┘
          │                  │                  │                  │
          ▼                  ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    INGESTION LAYER                                          │
│                    (Apache Airflow DAGs)                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │  Batch Ingestion Jobs (Databricks SubmitRunOperator)              │   │
│  │  - ingest_orders                                                   │   │
│  │  - ingest_customers                                                │   │
│  │  - ingest_inventory                                                │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │  Streaming Ingestion (Structured Streaming)                        │   │
│  │  - stream_sales_transactions (Kafka → Delta)                       │   │
│  └────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│              DELTA LAKE STORAGE (Medallion Architecture)                    │
│              Unity Catalog: retail_datalake                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │  BRONZE LAYER (Raw/Ingested Data)                                  │   │
│  │  Schema: {env}_bronze                                               │   │
│  │  - orders (raw JSON/Parquet)                                        │   │
│  │  - customers (raw JSON/Parquet)                                     │   │
│  │  - inventory (raw JSON/Parquet)                                     │   │
│  │  - sales_transactions (streaming events)                            │   │
│  │  Features:                                                          │   │
│  │  - Change Data Feed (CDF) enabled                                   │   │
│  │  - Time travel enabled                                              │   │
│  │  - Schema evolution supported                                       │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │  SILVER LAYER (Cleaned/Refined Data)                               │   │
│  │  Schema: {env}_silver                                               │   │
│  │  - orders (cleaned, validated, deduplicated)                        │   │
│  │  - customers (cleaned, validated, deduplicated)                     │   │
│  │  - inventory (cleaned, validated)                                   │   │
│  │  - sales_transactions (cleaned streaming events)                    │   │
│  │  Features:                                                          │   │
│  │  - Data type conversion                                             │   │
│  │  - Data validation                                                  │   │
│  │  - Deduplication                                                    │   │
│  │  - Canonical staging                                                │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │  GOLD LAYER (Business-Level Tables)                                │   │
│  │  Schema: {env}_gold                                                 │   │
│  │                                                                     │   │
│  │  Dimensions (SCD):                                                  │   │
│  │  - dim_customer (SCD Type 2: historical changes)                   │   │
│  │  - dim_product (SCD Type 2: historical changes)                    │   │
│  │  - dim_store (SCD Type 1: overwrite)                               │   │
│  │  - dim_date (static dimension)                                     │   │
│  │                                                                     │   │
│  │  Facts:                                                             │   │
│  │  - fact_sales (star schema: sales transactions)                    │   │
│  │                                                                     │   │
│  │  Aggregates:                                                        │   │
│  │  - agg_daily_sales (data marts for BI)                             │   │
│  │                                                                     │   │
│  │  Features:                                                          │   │
│  │  - Optimized for query performance                                 │   │
│  │  - Partitioned and Z-ordered                                       │   │
│  │  - Indexed for fast lookups                                        │   │
│  └────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SERVING / ANALYTICAL LAYER                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │  Databricks SQL Warehouses                                         │   │
│  │  - Analytics warehouse (auto-scaling)                              │   │
│  │  - Query Gold layer tables                                         │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │  BI Tools                                                          │   │
│  │  - Tableau / Power BI / Looker                                    │   │
│  │  - Connect via JDBC/ODBC to SQL Warehouse                          │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │  Delta Sharing                                                     │   │
│  │  - Share Gold tables with external partners                        │   │
│  │  - Secure, real-time data sharing                                 │   │
│  └────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION (Apache Airflow)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │  DAG: retail_ingestion_pipeline                                     │   │
│  │  - Schedule: Hourly                                                │   │
│  │  - Tasks: Batch ingestion jobs (parallel)                          │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │  DAG: retail_transformation_pipeline                                │   │
│  │  - Schedule: Every 2 hours                                         │   │
│  │  - Tasks: Bronze → Silver → Gold transformations                   │   │
│  │  - Dependencies: Dimensions before Facts                           │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │  DAG: retail_data_quality_checks                                    │   │
│  │  - Schedule: Every 2 hours (after transformations)                 │   │
│  │  - Tasks: Quality validation, referential integrity                │   │
│  └────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    GOVERNANCE & METADATA                                    │
│                    (Unity Catalog)                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  - Table-level permissions                                                  │
│  - Schema-level access control                                              │
│  - Column-level security (masking PII)                                      │
│  - Row-level security                                                        │
│  - Data lineage tracking                                                    │
│  - Audit logging                                                            │
│  - Delta Sharing management                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Ingestion Layer

**Batch Ingestion:**
- Databricks notebooks for batch ingestion from source systems
- Support for JDBC connections (PostgreSQL, MySQL, etc.)
- CSV/Parquet file ingestion from S3/ADLS/GCS
- Airflow orchestration with retry logic

**Streaming Ingestion:**
- Spark Structured Streaming from Kafka
- Real-time CDC (Change Data Capture) processing
- Delta Lake streaming writes
- Checkpoint management for fault tolerance

### 2. Delta Lake Storage (Medallion Architecture)

**Bronze Layer:**
- Raw, unprocessed data
- Supports schema evolution
- Change Data Feed (CDF) enabled for CDC
- Time travel for auditing

**Silver Layer:**
- Cleaned and validated data
- Data type conversion
- Deduplication
- Canonical data model

**Gold Layer:**
- Business-level tables
- Star schema (facts and dimensions)
- SCD Type 1 and Type 2 support
- Optimized for analytics

### 3. Transformation Layer

**Bronze → Silver:**
- Data cleaning and validation
- Schema normalization
- Deduplication
- Data type conversion

**Silver → Gold:**
- Dimension table construction (SCD Type 1/2)
- Fact table construction
- Surrogate key generation
- Join with dimensions
- Measure calculation

### 4. Orchestration (Apache Airflow)

**DAGs:**
- `retail_ingestion_pipeline`: Batch and streaming ingestion
- `retail_transformation_pipeline`: Bronze → Silver → Gold
- `retail_data_quality_checks`: Quality validation

**Features:**
- Retry logic with exponential backoff
- Email/Slack notifications on failure
- Job dependency management
- Environment-specific configurations

### 5. Serving Layer

**Databricks SQL Warehouses:**
- Serverless compute for analytics
- Auto-scaling based on query load
- Query Gold layer tables
- JDBC/ODBC connectivity for BI tools

**BI Integration:**
- Tableau, Power BI, Looker support
- Real-time queries on Gold tables
- Cached queries for performance

### 6. Governance (Unity Catalog)

**Access Control:**
- Catalog-level permissions
- Schema-level permissions
- Table-level permissions
- Column-level security (PII masking)
- Row-level security

**Lineage & Audit:**
- Automatic lineage tracking
- Table-to-table dependencies
- Notebook-to-table lineage
- Query lineage
- Audit logs for compliance

## Data Flow

1. **Ingestion**: Source data → Bronze layer (Delta tables)
2. **Transformation 1**: Bronze → Silver (cleaning, validation)
3. **Transformation 2**: Silver → Gold (dimensions, facts)
4. **Quality Checks**: Validation after transformations
5. **Serving**: Gold tables → SQL Warehouse → BI tools

## Technology Stack

- **Storage**: Delta Lake on S3/ADLS/GCS
- **Compute**: Databricks Spark clusters
- **Orchestration**: Apache Airflow
- **Governance**: Unity Catalog
- **Analytics**: Databricks SQL Warehouses
- **CI/CD**: GitHub Actions
- **IaC**: Terraform

## Environments

- **Dev**: Development environment for testing
- **QA**: Quality assurance environment for validation
- **Prod**: Production environment for live data

Each environment has:
- Separate Databricks workspace (or catalog isolation)
- Separate Airflow instance
- Separate S3 buckets
- Environment-specific configurations

## Scaling & Performance

**Compute Scaling:**
- Auto-scaling clusters for jobs
- Serverless SQL warehouses
- Spot instances for cost optimization

**Storage Optimization:**
- Delta Lake file compaction
- Z-ordering for query performance
- Partitioning by date/region
- Caching for frequently accessed data

**Cost Optimization:**
- Cluster auto-termination
- Spot instances
- Query result caching
- Incremental processing

## Security

- Unity Catalog for access control
- IAM roles for AWS integration
- Secrets management via Databricks secrets
- Encryption at rest and in transit
- Audit logging for compliance

## Monitoring & Observability

- Airflow task monitoring
- Databricks job metrics
- Data quality metrics
- Query performance monitoring
- Cost tracking


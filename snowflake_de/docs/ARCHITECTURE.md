# Architecture Documentation

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         INGESTION LAYER                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │
│  │   POS System │  │ Order System │  │ Inventory DB │                   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                   │
│         │                 │                 │                            │
│         └─────────────────┼─────────────────┘                            │
│                           │                                              │
│                    ┌──────▼───────┐                                      │
│                    │ Cloud Storage │                                      │
│                    │  (S3/GCS/Azure)│                                     │
│                    │  External Stage │                                    │
│                    └──────┬───────┘                                      │
│                           │                                              │
│                    ┌──────▼───────┐                                      │
│                    │   Snowpipe   │                                      │
│                    │  (Auto Ingest)│                                     │
│                    └──────┬───────┘                                      │
└───────────────────────────┼────────────────────────────────────────────┘
                             │
┌───────────────────────────▼────────────────────────────────────────────┐
│                      SNOWFLAKE DATA PLATFORM                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    BRONZE LAYER (Raw Landing)                   │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │   │
│  │  │ raw_pos      │  │ raw_orders   │  │ raw_inventory│          │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │   │
│  └─────────┼──────────────────┼─────────────────┼──────────────────┘   │
│            │                  │                 │                        │
│            │  ┌───────────────▼─────────────────▼──────┐                │
│            │  │         Snowflake Streams             │                │
│            │  │      (Change Data Capture)             │                │
│            │  └───────────────┬─────────────────┬──────┘                │
│            │                  │                 │                        │
│  ┌─────────▼──────────────────▼─────────────────▼──────────────────┐   │
│  │                    SILVER LAYER (Staging/Cleaned)                 │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │   │
│  │  │ stg_pos      │  │ stg_orders   │  │ stg_inventory│          │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │   │
│  └─────────┼──────────────────┼─────────────────┼──────────────────┘   │
│            │                  │                 │                        │
│            │  ┌───────────────▼─────────────────▼──────┐                │
│            │  │      Snowflake Tasks (Transformations)  │                │
│            │  └───────────────┬─────────────────┬──────┘                │
│            │                  │                 │                        │
│  ┌─────────▼──────────────────▼─────────────────▼──────────────────┐   │
│  │                    GOLD LAYER (Curated/Dimensional)              │   │
│  │                                                                   │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │   │
│  │  │ dim_customer │  │ dim_product  │  │ dim_store    │          │   │
│  │  │ (SCD Type 2) │  │ (SCD Type 1) │  │ (SCD Type 2) │          │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │   │
│  │         │                  │                 │                   │   │
│  │         └──────────────────┼─────────────────┘                   │   │
│  │                            │                                     │   │
│  │                    ┌───────▼────────┐                            │   │
│  │                    │  fact_sales    │                            │   │
│  │                    │  fact_orders   │                            │   │
│  │                    └────────────────┘                            │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │              Virtual Warehouses (Compute)                        │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │   │
│  │  │ WH_INGEST│  │ WH_TRANS │  │ WH_ANALYT│  │ WH_LOAD   │       │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                             │
┌───────────────────────────▼────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER (AIRFLOW)                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                         Airflow DAGs                              │   │
│  │                                                                   │   │
│  │  ┌───────────────────────────────────────────────────────────┐  │   │
│  │  │  ingestion_dag                                            │  │   │
│  │  │  ├─ stage_files                                           │  │   │
│  │  │  ├─ trigger_snowpipe                                      │  │   │
│  │  │  └─ validate_ingestion                                    │  │   │
│  │  └───────────────────────────────────────────────────────────┘  │   │
│  │                                                                   │   │
│  │  ┌───────────────────────────────────────────────────────────┐  │   │
│  │  │  transformation_dag                                        │  │   │
│  │  │  ├─ bronze_to_silver                                       │  │   │
│  │  │  ├─ silver_to_gold                                         │  │   │
│  │  │  ├─ load_dimensions                                        │  │   │
│  │  │  ├─ load_facts                                             │  │   │
│  │  │  └─ data_quality_checks                                     │  │   │
│  │  └───────────────────────────────────────────────────────────┘  │   │
│  │                                                                   │   │
│  │  ┌───────────────────────────────────────────────────────────┐  │   │
│  │  │  monitoring_dag                                            │  │   │
│  │  │  ├─ check_pipeline_health                                  │  │   │
│  │  │  ├─ alert_on_failures                                      │  │   │
│  │  │  └─ generate_metrics                                       │  │   │
│  │  └───────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                             │
┌───────────────────────────▼────────────────────────────────────────────┐
│                    CONSUMPTION LAYER                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ BI Tools     │  │ Data Science │  │ Applications │                  │
│  │ (Tableau,    │  │ (Jupyter,    │  │ (APIs,       │                  │
│  │  Power BI)   │  │  Snowpark)   │  │  Reports)    │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Ingestion Layer

**Batch Ingestion**:
- Files from source systems (POS, Orders, Inventory) are staged in cloud object storage
- Snowpipe automatically ingests files from external stages into Snowflake raw tables
- Supports CSV, JSON, Parquet formats

**Streaming/CDC Ingestion**:
- Snowflake Streams detect changes in raw tables
- Tasks process incremental changes in real-time
- Supports change data capture patterns

### 2. Data Lake / Raw Storage (Bronze)

- **Purpose**: Store raw, unprocessed data exactly as received
- **Storage**: Snowflake internal tables with VARIANT columns for semi-structured data
- **Schema**: `{ENV}_RAW` database
- **Tables**: `raw_pos`, `raw_orders`, `raw_inventory`, etc.

### 3. Staging Layer (Silver)

- **Purpose**: Cleaned, standardized, and validated data
- **Schema**: `{ENV}_STAGING` database
- **Transformations**:
  - Data type standardization
  - Null handling
  - Deduplication
  - Business rule validation
- **Tables**: `stg_pos`, `stg_orders`, `stg_inventory`, etc.

### 4. Data Warehouse (Gold)

- **Purpose**: Business-ready dimensional models
- **Schema**: `{ENV}_DW` database
- **Design**: Star schema with fact and dimension tables
- **SCD Support**:
  - Type 1: Overwrite (for corrections)
  - Type 2: Historical tracking (with effective dates)

### 5. Orchestration (Airflow)

- **DAGs**: Modular, reusable pipeline definitions
- **Operators**: SnowflakeOperator, SQLExecuteQueryOperator
- **Features**:
  - Retry logic
  - Failure notifications
  - Dynamic task mapping
  - Data quality checks

### 6. Virtual Warehouses

- **WH_INGEST**: For data ingestion workloads
- **WH_TRANS**: For transformation workloads
- **WH_ANALYT**: For analytics queries
- **WH_LOAD**: For bulk loading operations

### 7. Environment Strategy

- **Dev**: Development and testing
- **QA**: Quality assurance
- **Prod**: Production
- **Cloning**: Zero-copy cloning for environment promotion

## Data Flow

1. **Ingestion**: Source → Cloud Storage → Snowpipe → Bronze
2. **Transformation**: Bronze → (Streams/Tasks) → Silver → Gold
3. **Orchestration**: Airflow coordinates all steps
4. **Consumption**: Gold layer → BI Tools / Applications

## Technology Stack

- **Data Platform**: Snowflake
- **Orchestration**: Apache Airflow
- **Storage**: Cloud Object Storage (S3/GCS/Azure) + Snowflake
- **Infrastructure**: Terraform
- **CI/CD**: GitHub Actions
- **Version Control**: Git


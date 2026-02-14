# Architecture Documentation

## System Architecture

### Data Flow

1. **Ingestion Phase**
   - Source systems (POS, Orders, Inventory) generate transactional data
   - Batch ingestion: Scheduled Airflow DAGs pull data via APIs/files/DBs
   - CDC ingestion: Change Data Capture streams capture real-time changes
   - Data lands in **Bronze Layer** (raw, unprocessed)

2. **Data Lake (Medallion Architecture)**
   - **Bronze (Raw)**: Original data, schema-on-read, partitioned by date/source
   - **Silver (Clean)**: Cleaned, validated, deduplicated data
   - **Gold (Curated)**: Business-ready, aggregated data

3. **Transformation Phase (dbt)**
   - dbt reads from Silver/Gold layer or directly from warehouse staging
   - **Staging Models**: Raw → clean, type casting, basic validations
   - **Intermediate Models**: Business logic, joins, calculations
   - **Dimension Models**: SCD Type 1 and Type 2 dimensions
   - **Fact Models**: Transactional facts, snapshots
   - **Mart Models**: Aggregated, business-friendly tables

4. **Data Warehouse**
   - Final models materialized as tables/views
   - Partitioned and clustered for performance
   - Served to BI tools and analytics platforms

### Technology Stack

- **Ingestion**: Python scripts, Airflow operators, CDC connectors
- **Data Lake**: Cloud object storage (S3/GCS/ADLS) with Parquet/Delta format
- **Transformation**: dbt (Data Build Tool)
- **Orchestration**: Apache Airflow
- **Warehouse**: Snowflake/BigQuery/Redshift (configurable)
- **CI/CD**: GitHub Actions
- **Version Control**: Git

### Environment Architecture

```
┌─────────────────────────────────────────────────┐
│                    Git Repo                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │   Dev    │→ │    QA    │→ │   Prod   │      │
│  └──────────┘  └──────────┘  └──────────┘      │
└─────────────────────────────────────────────────┘
         │              │              │
         ▼              ▼              ▼
┌─────────────────────────────────────────────────┐
│              Airflow Environments                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Dev DAGs │  │ QA DAGs   │  │ Prod DAGs│      │
│  └──────────┘  └──────────┘  └──────────┘      │
└─────────────────────────────────────────────────┘
         │              │              │
         ▼              ▼              ▼
┌─────────────────────────────────────────────────┐
│            dbt Target Schemas                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ dev_schema│ │ qa_schema │ │prod_schema│     │
│  └──────────┘  └──────────┘  └──────────┘      │
└─────────────────────────────────────────────────┘
```

### SCD Implementation Strategy

- **SCD Type 1**: Overwrite historical values (e.g., customer address updates)
- **SCD Type 2**: Maintain full history with `valid_from`, `valid_to`, `current_flag`
- **SCD Type 3**: Limited history (not implemented, but extensible)

### Data Quality Framework

- **dbt Tests**: Built-in (unique, not_null, relationships) + custom SQL tests
- **Airflow Quality Checks**: Row counts, freshness, anomaly detection
- **Test Execution**: After each model build, tests run automatically
- **Failure Handling**: Alerts, retries, notifications

### Orchestration Flow

```
Airflow DAG:
├── Ingestion Task
│   └── Load raw data to Bronze
├── dbt Staging Task
│   └── dbt run --select staging.*
├── dbt Staging Tests
│   └── dbt test --select staging.*
├── dbt Dimensions Task
│   └── dbt run --select dimensions.*
├── dbt Facts Task
│   └── dbt run --select facts.*
├── dbt Marts Task
│   └── dbt run --select marts.*
├── dbt Final Tests
│   └── dbt test
└── dbt Docs Generation
    └── dbt docs generate
```


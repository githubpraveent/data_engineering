# Retail Data Lake + Data Warehouse Solution

A comprehensive data engineering solution using dbt for transformations and Apache Airflow for orchestration.

## Architecture Overview

### High-Level Flow

```
┌─────────────────┐
│ Source Systems  │
│ - POS Systems   │
│ - Order Systems │
│ - Inventory     │
└────────┬────────┘
         │
         │ (Batch/CDC Ingestion)
         ▼
┌─────────────────┐
│  Data Lake      │
│  (S3/GCS/ADLS)  │
│                 │
│  Bronze (Raw)   │
│  Silver (Clean) │
│  Gold (Curated) │
└────────┬────────┘
         │
         │ (dbt reads from lake/warehouse)
         ▼
┌─────────────────┐
│ Data Warehouse  │
│ (Snowflake/     │
│  BigQuery/etc)  │
│                 │
│  Staging        │
│  Dimensions     │
│  Facts          │
│  Marts          │
└────────┬────────┘
         │
         │ (BI Tools, Analytics)
         ▼
┌─────────────────┐
│  Consumers      │
│  (Dashboards,   │
│   Reports)      │
└─────────────────┘
```

### Components

1. **Ingestion Layer**: Airflow DAGs + scripts for batch/CDC ingestion into data lake
2. **Data Lake**: Medallion architecture (Bronze/Silver/Gold) for raw data storage
3. **Transformation Layer**: dbt models organized in layers (staging → intermediate → dims → facts → marts)
4. **Data Warehouse**: Analytical store where dbt materializes final models
5. **Orchestration**: Airflow manages the entire pipeline with dependencies
6. **CI/CD**: GitHub Actions for automated testing and deployment
7. **Environments**: Dev, QA, Prod with separate schemas/targets

### Environment Strategy

- **Dev**: Development schema, feature branches
- **QA**: QA schema, staging branch
- **Prod**: Production schema, main branch

Each environment uses separate dbt targets and Airflow connections.

## Project Structure

```
.
├── dbt_project/              # dbt project
│   ├── models/
│   │   ├── staging/
│   │   ├── intermediate/
│   │   ├── dimensions/
│   │   ├── facts/
│   │   └── marts/
│   ├── tests/
│   ├── macros/
│   ├── snapshots/
│   └── dbt_project.yml
├── airflow/
│   ├── dags/
│   ├── plugins/
│   └── requirements.txt
├── ingestion/
│   ├── scripts/
│   └── connectors/
├── .github/
│   └── workflows/
├── docs/
│   └── runbook.md
└── docker-compose.yml        # Local development setup
```

## Quick Start

### Prerequisites

- Python 3.9+
- dbt (with appropriate adapter)
- Apache Airflow
- Data warehouse access (Snowflake/BigQuery/etc)

### Setup

1. **Configure dbt profiles**:
   ```bash
   cp dbt_project/profiles.example.yml ~/.dbt/profiles.yml
   # Edit with your warehouse credentials
   ```

2. **Set up Airflow**:
   ```bash
   cd airflow
   pip install -r requirements.txt
   export AIRFLOW_HOME=$(pwd)
   airflow db init
   ```

3. **Run dbt**:
   ```bash
   cd dbt_project
   dbt deps
   dbt run
   dbt test
   ```

## Documentation

- [Architecture Details](docs/architecture.md)
- [Runbook](docs/runbook.md)
- [dbt Documentation](dbt_project/README.md)


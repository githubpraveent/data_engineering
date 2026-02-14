# Retail Data Lake + Data Warehouse on Snowflake

A scalable retail data engineering solution using Snowflake as the core data platform with Apache Airflow and Dagster for orchestration.

## Architecture Overview

This solution implements a medallion (Bronze-Silver-Gold) architecture:

- **Bronze (Raw Landing)**: Raw data ingestion from operational systems
- **Silver (Staging/Cleaned)**: Cleaned, standardized, and validated data
- **Gold (Curated)**: Business-ready dimensional models with SCD Type 1/2 support

## Project Structure

```
.
├── airflow/
│   ├── dags/                    # Airflow DAG definitions
│   ├── plugins/                 # Custom Airflow operators/plugins
│   └── config/                  # Airflow configuration
├── dagster/
│   ├── assets/                  # Dagster asset definitions
│   ├── jobs/                    # Dagster job definitions
│   ├── definitions.py           # Dagster definitions entry point
│   └── dagster.yaml             # Dagster configuration
├── snowflake/
│   ├── ddl/                     # Database, schema, warehouse definitions
│   ├── sql/
│   │   ├── bronze/              # Raw landing layer SQL
│   │   ├── silver/              # Staging/cleaned layer SQL
│   │   ├── gold/                # Dimensional model SQL
│   │   └── streams_tasks/       # Streams and Tasks definitions
│   └── stored_procedures/       # Reusable stored procedures
├── terraform/                   # Infrastructure as Code
├── tests/                       # Testing scripts and data quality checks
├── ci_cd/                       # CI/CD pipeline definitions
├── docs/                        # Documentation
└── scripts/                     # Utility scripts

```

## Quick Start

### Prerequisites

- Snowflake account with appropriate privileges
- Apache Airflow instance (or local development environment) OR Dagster
- Python 3.8+
- Terraform (for infrastructure provisioning)

### Setup

1. **Configure Snowflake Connection**:
   ```bash
   cp airflow/config/snowflake_connection.example.json airflow/config/snowflake_connection.json
   # Edit with your Snowflake credentials
   ```

2. **Deploy Snowflake Infrastructure**:
   ```bash
   cd terraform
   terraform init
   terraform plan
   terraform apply
   ```

3. **Run Snowflake DDL Scripts**:
   ```bash
   snowflake-sql-runner --env dev --file snowflake/ddl/01_setup_warehouses.sql
   ```

4. **Deploy Orchestration**:
   
   **Option A: Airflow**
   ```bash
   cp -r airflow/dags/* /path/to/airflow/dags/
   ```
   
   **Option B: Dagster**
   ```bash
   ./scripts/setup_dagster.sh
   dagster dev -f dagster/definitions.py
   ```

## Environments

- **Development (DEV)**: For development and testing
- **QA**: For quality assurance and integration testing
- **Production (PROD)**: Production environment

## Key Features

- ✅ Batch and streaming ingestion
- ✅ Medallion architecture (Bronze → Silver → Gold)
- ✅ SCD Type 1 and Type 2 dimension loads
- ✅ Data quality checks and validation
- ✅ CI/CD with GitHub Actions
- ✅ Environment promotion (Dev → QA → Prod)
- ✅ Zero-copy cloning for environments
- ✅ Monitoring and alerting

## Documentation

See `docs/` directory for detailed documentation:
- Architecture diagrams
- Runbooks
- Testing plans
- Governance policies

## License

MIT


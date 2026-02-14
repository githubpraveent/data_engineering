# Setup Guide

This guide walks you through setting up the retail data warehouse solution.

## Prerequisites

- Python 3.9+
- Git
- Docker and Docker Compose (for local Airflow)
- Access to a data warehouse (Snowflake, BigQuery, Redshift, etc.)
- Access to data lake storage (S3, GCS, Azure Data Lake, etc.)

## Step 1: Clone and Setup Repository

```bash
git clone <repository-url>
cd cursor_DBT_DE
```

## Step 2: Configure dbt

1. **Install dbt**:
   ```bash
   pip install dbt-core dbt-snowflake
   # Or for other warehouses:
   # pip install dbt-bigquery
   # pip install dbt-redshift
   ```

2. **Configure profiles**:
   ```bash
   mkdir -p ~/.dbt
   cp dbt_project/profiles.example.yml ~/.dbt/profiles.yml
   ```

3. **Edit profiles.yml** with your warehouse credentials:
   - Update account, user, password, database, warehouse, schema
   - Configure dev, qa, and prod targets

4. **Install dbt packages**:
   ```bash
   cd dbt_project
   dbt deps
   ```

5. **Test connection**:
   ```bash
   dbt debug --target dev
   ```

## Step 3: Setup Airflow (Local Development)

1. **Set environment variables**:
   ```bash
   export AIRFLOW_UID=$(id -u)
   export AIRFLOW_PROJ_DIR=$(pwd)
   ```

2. **Start Airflow**:
   ```bash
   docker-compose up -d
   ```

3. **Access Airflow UI**:
   - Open http://localhost:8080
   - Login: airflow / airflow

4. **Configure Airflow Variables**:
   - In Airflow UI: Admin → Variables
   - Add variables:
     - `DBT_ENVIRONMENT`: dev
     - `DBT_PROJECT_DIR`: /opt/airflow/dbt_project
     - `DATA_LAKE_BUCKET`: your-bucket-name
     - `INGESTION_SCRIPT_DIR`: /opt/airflow/ingestion/scripts

## Step 4: Create Source Tables

Before running dbt, you need to create the source tables in your data lake/warehouse. These represent the bronze layer.

Example for Snowflake:
```sql
CREATE SCHEMA IF NOT EXISTS retail_db.bronze;

CREATE TABLE IF NOT EXISTS retail_db.bronze.orders (
    order_id INTEGER,
    customer_id INTEGER,
    store_id INTEGER,
    order_date DATE,
    total_amount DECIMAL(10, 2),
    status VARCHAR(50)
);

-- Create other source tables similarly
```

## Step 5: Run Initial dbt Models

1. **Run staging models**:
   ```bash
   cd dbt_project
   dbt run --select tag:staging --target dev
   ```

2. **Run tests**:
   ```bash
   dbt test --select tag:staging --target dev
   ```

3. **Run all models**:
   ```bash
   dbt run --target dev
   dbt test --target dev
   ```

## Step 6: Configure Ingestion

1. **Update ingestion scripts** with your source system connections
2. **Test ingestion locally**:
   ```bash
   python ingestion/scripts/ingest_orders.py \
       --start-date 2024-01-01 \
       --end-date 2024-01-01
   ```

## Step 7: Setup CI/CD

1. **Configure GitHub Secrets**:
   - Go to repository Settings → Secrets
   - Add secrets:
     - `SNOWFLAKE_PASSWORD`: Your Snowflake password
     - Other warehouse credentials as needed

2. **CI/CD will run automatically** on PRs and pushes

## Step 8: Generate Documentation

```bash
cd dbt_project
dbt docs generate --target dev
dbt docs serve
```

Access documentation at http://localhost:8080

## Environment Setup

### Development
- Branch: `develop` or feature branches
- dbt target: `dev`
- Schema: `dev_schema`

### QA
- Branch: `develop` (merged from feature branches)
- dbt target: `qa`
- Schema: `qa_schema`

### Production
- Branch: `main`
- dbt target: `prod`
- Schema: `prod_schema`

## Troubleshooting

### dbt Connection Issues
- Verify credentials in `~/.dbt/profiles.yml`
- Test connection: `dbt debug`
- Check network/firewall settings

### Airflow DAG Not Appearing
- Check DAG files are in `airflow/dags/`
- Verify DAG syntax: `python -c "from airflow.models import DagBag; d = DagBag(); d.dags"`
- Check Airflow logs

### Model Build Failures
- Check source data exists
- Verify source table schemas match dbt source definitions
- Review dbt logs: `dbt_project/logs/`

## Next Steps

1. Review [Architecture Documentation](docs/architecture.md)
2. Read [Runbook](docs/runbook.md) for operational procedures
3. Customize models for your specific data sources
4. Set up monitoring and alerts


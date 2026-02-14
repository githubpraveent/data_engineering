# Quick Start Guide

This guide will help you get started with the retail data lake and data warehouse solution.

## Prerequisites

- Snowflake account with appropriate privileges
- Apache Airflow instance (or local development environment)
- Python 3.8+
- Terraform (optional, for infrastructure provisioning)
- Git

## Step 1: Clone and Setup

```bash
# Clone the repository (if using version control)
git clone <repository-url>
cd cursor_snowflake_DE

# Run setup script
./scripts/setup_environment.sh
```

## Step 2: Configure Snowflake

1. **Update Snowflake Connection**
   - Edit `.env` file with your Snowflake credentials
   - Or configure SnowSQL config file

2. **Run DDL Scripts**
   ```bash
   # Execute all DDL scripts in order
   ./scripts/run_snowflake_ddl.sh DEV
   ```

   Or manually execute:
   ```bash
   # Using SnowSQL
   snowsql -c ~/.snowsql/config -f snowflake/ddl/01_setup_warehouses.sql
   snowsql -c ~/.snowsql/config -f snowflake/ddl/02_setup_databases_schemas.sql
   # ... continue with other scripts
   ```

## Step 3: Configure Airflow

1. **Set Airflow Connection**
   ```bash
   airflow connections add snowflake_default \
     --conn-type snowflake \
     --conn-login <your_user> \
     --conn-password <your_password> \
     --conn-extra '{"account": "<your_account>", "warehouse": "WH_TRANS", "database": "DEV_RAW"}'
   ```

2. **Set Airflow Variables**
   ```bash
   airflow variables set ENVIRONMENT DEV
   ```

3. **Copy DAGs**
   ```bash
   # If Airflow is running elsewhere, copy DAGs
   cp -r airflow/dags/* /path/to/airflow/dags/
   ```

4. **Start Airflow**
   ```bash
   # Start webserver
   airflow webserver --port 8080

   # In another terminal, start scheduler
   airflow scheduler
   ```

## Step 4: Configure External Stages (Optional)

If using cloud object storage:

1. **Create Storage Integration** (one-time setup)
   ```sql
   -- AWS S3 example
   CREATE STORAGE INTEGRATION s3_integration
     TYPE = EXTERNAL_STAGE
     STORAGE_PROVIDER = 'S3'
     STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::123456789012:role/snowflake-role'
     ENABLED = TRUE
     STORAGE_ALLOWED_LOCATIONS = ('s3://your-bucket/raw/');
   ```

2. **Update External Stage URLs**
   - Edit `snowflake/ddl/04_setup_external_stage.sql`
   - Update URLs to match your bucket locations

## Step 5: Populate Date Dimension

```sql
-- Connect to Snowflake and run
USE DATABASE DEV_DW;
USE SCHEMA DIMENSIONS;

-- Populate date dimension for 5 years
CALL sp_populate_date_dimension('2020-01-01'::DATE, '2025-12-31'::DATE);
```

## Step 6: Test the Pipeline

1. **Upload Test Data**
   - Place test CSV/JSON files in your cloud storage bucket
   - Or manually load data:
   ```sql
   COPY INTO DEV_RAW.BRONZE.raw_pos
   FROM @DEV_RAW.BRONZE.stage_pos_data
   FILES = ('test_pos_data.csv')
   FILE_FORMAT = (FORMAT_NAME = 'csv_format');
   ```

2. **Trigger Airflow DAGs**
   - Go to Airflow UI (http://localhost:8080)
   - Trigger `retail_ingestion_pipeline` DAG
   - Monitor execution

3. **Verify Data Flow**
   ```sql
   -- Check raw data
   SELECT COUNT(*) FROM DEV_RAW.BRONZE.raw_pos;

   -- Check staging data
   SELECT COUNT(*) FROM DEV_STAGING.SILVER.stg_pos;

   -- Check fact data
   SELECT COUNT(*) FROM DEV_DW.FACTS.fact_sales;
   ```

## Step 7: Run Data Quality Checks

```sql
-- Run data quality test queries
-- See tests/data_quality/test_data_quality_checks.sql

-- Or trigger Airflow data quality DAG
-- retail_data_quality_monitoring
```

## Using Terraform (Optional)

If you prefer Infrastructure as Code:

1. **Configure Terraform**
   ```bash
   cd terraform/snowflake
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   ```

2. **Initialize and Apply**
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

## Environment Promotion

### Dev → QA

1. **Clone Databases**
   ```sql
   CREATE DATABASE QA_RAW CLONE DEV_RAW;
   CREATE DATABASE QA_STAGING CLONE DEV_STAGING;
   CREATE DATABASE QA_DW CLONE DEV_DW;
   ```

2. **Update Airflow Variables**
   ```bash
   airflow variables set ENVIRONMENT QA
   ```

3. **Update CI/CD**
   - Merge `dev` branch to `qa` branch
   - CI/CD will automatically deploy

### QA → Production

1. **Get Approvals**
   - QA sign-off
   - Business approval
   - Security review

2. **Clone Databases**
   ```sql
   CREATE DATABASE PROD_RAW CLONE QA_RAW;
   CREATE DATABASE PROD_STAGING CLONE QA_STAGING;
   CREATE DATABASE PROD_DW CLONE QA_DW;
   ```

3. **Deploy via CI/CD**
   - Merge `qa` branch to `main` branch
   - CI/CD will deploy to production (with approval)

## Common Tasks

### Adding a New Source System

1. **Create Raw Table**
   - Add table definition in `snowflake/sql/bronze/01_create_raw_tables.sql`

2. **Create Staging Table**
   - Add table definition in `snowflake/sql/silver/01_create_staging_tables.sql`

3. **Create Transformation**
   - Add transformation logic in `snowflake/sql/silver/02_bronze_to_silver_transform.sql`

4. **Update Airflow DAGs**
   - Add tasks to ingestion and transformation DAGs

5. **Test and Deploy**
   - Test in Dev environment
   - Promote to QA and Production

### Monitoring Pipeline Health

1. **Airflow UI**
   - Check DAG execution status
   - View task logs
   - Monitor execution times

2. **Snowflake Queries**
   ```sql
   -- Check task execution
   SELECT * FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY())
   WHERE SCHEDULED_TIME >= CURRENT_TIMESTAMP() - INTERVAL '24 hours';

   -- Check pipe status
   SELECT SYSTEM$PIPE_STATUS('DEV_RAW.BRONZE.pipe_pos_data');

   -- Check data freshness
   SELECT MAX(load_timestamp) FROM DEV_RAW.BRONZE.raw_pos;
   ```

### Troubleshooting

**Issue: Pipeline not ingesting data**
- Check Snowpipe status
- Verify external stage configuration
- Check file format compatibility

**Issue: Transformation failing**
- Check task execution history
- Review validation errors in staging tables
- Verify data quality

**Issue: Dimension load errors**
- Check for overlapping SCD Type 2 records
- Verify referential integrity
- Review stored procedure logs

See `docs/RUNBOOK.md` for detailed troubleshooting procedures.

## Next Steps

1. **Review Documentation**
   - Architecture: `docs/ARCHITECTURE.md`
   - Runbook: `docs/RUNBOOK.md`
   - Testing: `docs/TESTING_PLAN.md`
   - Governance: `docs/GOVERNANCE.md`

2. **Customize for Your Needs**
   - Update table schemas to match your source systems
   - Adjust transformation logic
   - Add business-specific data quality checks

3. **Set Up Monitoring**
   - Configure alerts
   - Set up dashboards
   - Establish SLAs

4. **Onboard Team**
   - Train data engineers
   - Train data analysts
   - Document processes

## Support

For issues or questions:
- Review documentation in `docs/` directory
- Check runbook for common issues
- Contact data engineering team

## Additional Resources

- [Snowflake Documentation](https://docs.snowflake.com/)
- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [Terraform Snowflake Provider](https://registry.terraform.io/providers/Snowflake-Labs/snowflake/latest/docs)


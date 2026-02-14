# BigQuery SQL Scripts

This directory contains SQL scripts for schema creation, transformations, SCD logic, and fact table loads.

## Structure

- `schemas/`: Table creation scripts
  - `create_staging_tables.sql`: Staging tables for raw/lightly transformed data
  - `create_curated_tables.sql`: Curated tables (dimensions and facts)
  - `create_analytics_tables.sql`: Analytics/aggregated tables
- `transformations/`: Data transformation scripts
  - `load_date_dimension.sql`: Populate date dimension table
  - `update_analytics_tables.sql`: Update aggregated tables
- `scd/`: Slowly Changing Dimension scripts
  - `scd_type2_customer.sql`: SCD Type 2 for customer dimension
  - `scd_type2_product.sql`: SCD Type 2 for product dimension
  - `scd_type1_store.sql`: SCD Type 1 for store dimension
- `fact_loads/`: Fact table loading scripts
  - `load_sales_fact.sql`: Load sales fact table
  - `load_inventory_fact.sql`: Load inventory fact table

## Usage

### Parameter Substitution

All scripts use parameter placeholders that need to be replaced:
- `{project_id}`: GCP Project ID
- `{staging_dataset}`: Staging dataset name (e.g., `staging_dev`)
- `{curated_dataset}`: Curated dataset name (e.g., `curated_dev`)
- `{analytics_dataset}`: Analytics dataset name (e.g., `analytics_dev`)
- `{environment}`: Environment name (dev, qa, prod)
- `{load_date}`: Date for incremental loads (format: YYYY-MM-DD)

### Running Scripts

1. **Create tables (one-time setup):**
   ```bash
   bq query --use_legacy_sql=false --replace_parameters \
     --parameter=project_id:STRING:your-project-id \
     --parameter=staging_dataset:STRING:staging_dev \
     --parameter=curated_dataset:STRING:curated_dev \
     --parameter=environment:STRING:dev \
     < schemas/create_staging_tables.sql
   ```

2. **Run SCD updates (scheduled via Airflow):**
   ```bash
   bq query --use_legacy_sql=false --replace_parameters \
     --parameter=project_id:STRING:your-project-id \
     --parameter=staging_dataset:STRING:staging_dev \
     --parameter=curated_dataset:STRING:curated_dev \
     --parameter=load_date:DATE:2024-01-15 \
     < scd/scd_type2_customer.sql
   ```

3. **Load fact tables:**
   ```bash
   bq query --use_legacy_sql=false --replace_parameters \
     --parameter=project_id:STRING:your-project-id \
     --parameter=staging_dataset:STRING:staging_dev \
     --parameter=curated_dataset:STRING:curated_dev \
     --parameter=load_date:DATE:2024-01-15 \
     < fact_loads/load_sales_fact.sql
   ```

### Integration with Airflow

These scripts are called from Airflow DAGs using `BigQueryInsertJobOperator`. See `airflow/dags/` for examples.

### Best Practices

1. **Partitioning**: All fact tables are partitioned by date for performance and cost optimization
2. **Clustering**: Tables are clustered by frequently queried columns
3. **Incremental Loads**: Fact tables use incremental loads to avoid reprocessing
4. **SCD Type 2**: Customer and Product dimensions track history with effective/expiration dates
5. **SCD Type 1**: Store dimension overwrites current values (no history)


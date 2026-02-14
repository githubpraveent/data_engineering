#!/bin/bash

# ============================================================================
# Snowflake DDL Execution Script
# Executes Snowflake DDL scripts in the correct order
# ============================================================================

set -e

# Configuration
ENVIRONMENT=${1:-DEV}
SNOWSQL_CONFIG=${SNOWSQL_CONFIG:-~/.snowsql/config}

echo "Executing Snowflake DDL scripts for environment: $ENVIRONMENT"

# Function to execute SQL file
execute_sql() {
    local file=$1
    echo "Executing: $file"
    snowsql -c $SNOWSQL_CONFIG -f "$file" -o variable_substitution=true -o env=$ENVIRONMENT
}

# Execute DDL scripts in order
echo "Step 1: Setting up warehouses..."
execute_sql "snowflake/ddl/01_setup_warehouses.sql"

echo "Step 2: Setting up databases and schemas..."
execute_sql "snowflake/ddl/02_setup_databases_schemas.sql"

echo "Step 3: Setting up roles and permissions..."
execute_sql "snowflake/ddl/03_setup_roles_permissions.sql"

echo "Step 4: Setting up external stages..."
execute_sql "snowflake/ddl/04_setup_external_stage.sql"

echo "Step 5: Setting up Snowpipe..."
execute_sql "snowflake/ddl/05_setup_snowpipe.sql"

echo "Step 6: Creating Bronze layer tables..."
execute_sql "snowflake/sql/bronze/01_create_raw_tables.sql"

echo "Step 7: Creating Silver layer tables..."
execute_sql "snowflake/sql/silver/01_create_staging_tables.sql"

echo "Step 8: Creating Bronze to Silver transformations..."
execute_sql "snowflake/sql/silver/02_bronze_to_silver_transform.sql"

echo "Step 9: Creating Gold layer dimension tables..."
execute_sql "snowflake/sql/gold/01_create_dimension_tables.sql"

echo "Step 10: Creating SCD Type 2 stored procedures..."
execute_sql "snowflake/sql/gold/02_scd_type2_customer_load.sql"

echo "Step 11: Creating SCD Type 1 stored procedures..."
execute_sql "snowflake/sql/gold/03_scd_type1_product_load.sql"

echo "Step 12: Creating fact tables..."
execute_sql "snowflake/sql/gold/04_create_fact_tables.sql"

echo "Step 13: Creating fact load stored procedures..."
execute_sql "snowflake/sql/gold/05_load_fact_sales.sql"

echo "Step 14: Creating streams..."
execute_sql "snowflake/sql/streams_tasks/01_create_streams.sql"

echo "Step 15: Creating incremental tasks..."
execute_sql "snowflake/sql/streams_tasks/02_create_incremental_tasks.sql"

echo "All DDL scripts executed successfully!"


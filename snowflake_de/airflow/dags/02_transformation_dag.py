"""
Airflow DAG for Data Transformation
Orchestrates the transformation of data from Bronze → Silver → Gold layers
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup
from airflow.models import Variable

# Default arguments
default_args = {
    'owner': 'data_engineering',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'snowflake_conn_id': 'snowflake_default',
}

# Environment configuration
ENV = Variable.get("ENVIRONMENT", default_var="DEV")
RAW_DATABASE = f"{ENV}_RAW"
STAGING_DATABASE = f"{ENV}_STAGING"
DW_DATABASE = f"{ENV}_DW"

# DAG definition
dag = DAG(
    'retail_transformation_pipeline',
    default_args=default_args,
    description='Transform retail data from Bronze to Silver to Gold layers',
    schedule_interval=timedelta(hours=1),  # Run every hour
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['transformation', 'retail', 'snowflake'],
)


def execute_stored_procedure(procedure_name, database, schema, **context):
    """Execute a Snowflake stored procedure"""
    hook = SnowflakeHook(snowflake_conn_id='snowflake_default')
    
    query = f"CALL {database}.{schema}.{procedure_name}()"
    result = hook.get_first(query)
    
    print(f"Stored procedure {procedure_name} executed. Result: {result}")
    return result


# Task Group: Bronze to Silver Transformations
with TaskGroup('bronze_to_silver', dag=dag) as bronze_to_silver_group:
    # Transform POS data
    transform_pos = SnowflakeOperator(
        task_id='transform_pos',
        sql=f"""
        -- This task is handled by Snowflake Tasks, but we can trigger manually if needed
        EXECUTE TASK {STAGING_DATABASE}.TASKS.task_bronze_to_silver_pos;
        """,
        dag=dag,
    )
    
    # Transform Orders data
    transform_orders = SnowflakeOperator(
        task_id='transform_orders',
        sql=f"""
        EXECUTE TASK {STAGING_DATABASE}.TASKS.task_bronze_to_silver_orders;
        """,
        dag=dag,
    )
    
    # Transform Inventory data
    transform_inventory = SnowflakeOperator(
        task_id='transform_inventory',
        sql=f"""
        EXECUTE TASK {STAGING_DATABASE}.TASKS.task_bronze_to_silver_inventory;
        """,
        dag=dag,
    )


# Task Group: Silver Data Quality Checks
with TaskGroup('silver_data_quality', dag=dag) as silver_quality_group:
    # Validate POS staging data
    validate_stg_pos = SnowflakeOperator(
        task_id='validate_stg_pos',
        sql=f"""
        SELECT 
            COUNT(*) as total_rows,
            SUM(CASE WHEN is_valid = FALSE THEN 1 ELSE 0 END) as invalid_rows,
            SUM(CASE WHEN transaction_id IS NULL THEN 1 ELSE 0 END) as null_transaction_id,
            SUM(CASE WHEN store_id IS NULL THEN 1 ELSE 0 END) as null_store_id
        FROM {STAGING_DATABASE}.SILVER.stg_pos
        WHERE created_at >= CURRENT_TIMESTAMP() - INTERVAL '2 hours'
        HAVING invalid_rows > 0 OR null_transaction_id > 0 OR null_store_id > 0
        """,
        dag=dag,
    )
    
    # Validate Orders staging data
    validate_stg_orders = SnowflakeOperator(
        task_id='validate_stg_orders',
        sql=f"""
        SELECT 
            COUNT(*) as total_rows,
            SUM(CASE WHEN is_valid = FALSE THEN 1 ELSE 0 END) as invalid_rows,
            SUM(CASE WHEN order_id IS NULL THEN 1 ELSE 0 END) as null_order_id,
            SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) as null_customer_id
        FROM {STAGING_DATABASE}.SILVER.stg_orders
        WHERE created_at >= CURRENT_TIMESTAMP() - INTERVAL '2 hours'
        HAVING invalid_rows > 0 OR null_order_id > 0 OR null_customer_id > 0
        """,
        dag=dag,
    )


# Task Group: Load Dimensions
with TaskGroup('load_dimensions', dag=dag) as load_dimensions_group:
    # Load Customer Dimension (SCD Type 2)
    load_dim_customer = PythonOperator(
        task_id='load_dim_customer',
        python_callable=execute_stored_procedure,
        op_args=['sp_load_dim_customer_scd_type2', DW_DATABASE, 'DIMENSIONS'],
        dag=dag,
    )
    
    # Load Product Dimension (SCD Type 1)
    load_dim_product = PythonOperator(
        task_id='load_dim_product',
        python_callable=execute_stored_procedure,
        op_args=['sp_load_dim_product_scd_type1', DW_DATABASE, 'DIMENSIONS'],
        dag=dag,
    )
    
    # Load Store Dimension (SCD Type 2) - if procedure exists
    load_dim_store = SnowflakeOperator(
        task_id='load_dim_store',
        sql=f"""
        -- Placeholder for store dimension load
        -- CALL {DW_DATABASE}.DIMENSIONS.sp_load_dim_store_scd_type2();
        SELECT 'Store dimension load placeholder' as status;
        """,
        dag=dag,
    )


# Task Group: Load Facts
with TaskGroup('load_facts', dag=dag) as load_facts_group:
    # Load Fact Sales
    load_fact_sales = PythonOperator(
        task_id='load_fact_sales',
        python_callable=execute_stored_procedure,
        op_args=['sp_load_fact_sales', DW_DATABASE, 'FACTS'],
        dag=dag,
    )
    
    # Load Fact Orders
    load_fact_orders = SnowflakeOperator(
        task_id='load_fact_orders',
        sql=f"""
        -- Placeholder for orders fact load
        -- CALL {DW_DATABASE}.FACTS.sp_load_fact_orders();
        SELECT 'Orders fact load placeholder' as status;
        """,
        dag=dag,
    )


# Task Group: Gold Data Quality Checks
with TaskGroup('gold_data_quality', dag=dag) as gold_quality_group:
    # Validate referential integrity
    validate_referential_integrity = SnowflakeOperator(
        task_id='validate_referential_integrity',
        sql=f"""
        -- Check for orphaned fact records
        SELECT 
            'fact_sales' as fact_table,
            COUNT(*) as orphaned_records
        FROM {DW_DATABASE}.FACTS.fact_sales fs
        LEFT JOIN {DW_DATABASE}.DIMENSIONS.dim_product dp ON fs.product_key = dp.product_key
        LEFT JOIN {DW_DATABASE}.DIMENSIONS.dim_store ds ON fs.store_key = ds.store_key
        WHERE dp.product_key IS NULL OR ds.store_key IS NULL
        HAVING COUNT(*) > 0
        """,
        dag=dag,
    )
    
    # Validate fact row counts
    validate_fact_counts = SnowflakeOperator(
        task_id='validate_fact_counts',
        sql=f"""
        SELECT 
            'fact_sales' as table_name,
            COUNT(*) as row_count,
            MIN(created_at) as earliest_record,
            MAX(created_at) as latest_record
        FROM {DW_DATABASE}.FACTS.fact_sales
        WHERE created_at >= CURRENT_TIMESTAMP() - INTERVAL '2 hours'
        """,
        dag=dag,
    )


# Task dependencies
bronze_to_silver_group >> silver_quality_group >> load_dimensions_group >> load_facts_group >> gold_quality_group


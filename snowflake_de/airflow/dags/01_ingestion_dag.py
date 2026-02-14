"""
Airflow DAG for Data Ingestion
Orchestrates the ingestion of data from source systems into Snowflake
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
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
SNOWFLAKE_DATABASE = f"{ENV}_RAW"
SNOWFLAKE_SCHEMA = "BRONZE"

# DAG definition
dag = DAG(
    'retail_ingestion_pipeline',
    default_args=default_args,
    description='Ingest retail data from source systems into Snowflake',
    schedule_interval=timedelta(hours=1),  # Run every hour
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['ingestion', 'retail', 'snowflake'],
)


def check_snowpipe_status(**context):
    """Check Snowpipe status and file ingestion"""
    hook = SnowflakeHook(snowflake_conn_id='snowflake_default')
    
    # Check pipe status
    pipes = ['pipe_pos_data', 'pipe_orders_data', 'pipe_inventory_data']
    results = {}
    
    for pipe in pipes:
        query = f"""
        SELECT 
            SYSTEM$PIPE_STATUS('{SNOWFLAKE_DATABASE}.{SNOWFLAKE_SCHEMA}.{pipe}') as status
        """
        result = hook.get_first(query)
        results[pipe] = result[0] if result else None
    
    # Log results
    for pipe, status in results.items():
        print(f"Pipe {pipe} status: {status}")
    
    return results


def validate_ingestion(**context):
    """Validate that data was ingested successfully"""
    hook = SnowflakeHook(snowflake_conn_id='snowflake_default')
    
    # Check row counts for each raw table
    tables = ['raw_pos', 'raw_orders', 'raw_inventory']
    validation_results = {}
    
    for table in tables:
        query = f"""
        SELECT 
            COUNT(*) as row_count,
            MAX(load_timestamp) as latest_load
        FROM {SNOWFLAKE_DATABASE}.{SNOWFLAKE_SCHEMA}.{table}
        WHERE load_timestamp >= CURRENT_TIMESTAMP() - INTERVAL '2 hours'
        """
        result = hook.get_first(query)
        validation_results[table] = {
            'row_count': result[0] if result else 0,
            'latest_load': result[1] if result else None
        }
    
    # Log validation results
    for table, results in validation_results.items():
        print(f"Table {table}: {results['row_count']} rows, Latest load: {results['latest_load']}")
    
    # Fail if no data ingested in the last 2 hours (for hourly runs)
    total_rows = sum(r['row_count'] for r in validation_results.values())
    if total_rows == 0:
        raise ValueError("No data ingested in the last 2 hours")
    
    return validation_results


# Task: Check Snowpipe status
check_pipes = PythonOperator(
    task_id='check_snowpipe_status',
    python_callable=check_snowpipe_status,
    dag=dag,
)

# Task: Validate ingestion
validate_ingestion_task = PythonOperator(
    task_id='validate_ingestion',
    python_callable=validate_ingestion,
    dag=dag,
)

# Task: Data quality checks
data_quality_checks = SnowflakeOperator(
    task_id='data_quality_checks',
    sql="""
    -- Check for null critical fields
    SELECT 
        'raw_pos' as table_name,
        COUNT(*) as total_rows,
        SUM(CASE WHEN transaction_id IS NULL THEN 1 ELSE 0 END) as null_transaction_id,
        SUM(CASE WHEN store_id IS NULL THEN 1 ELSE 0 END) as null_store_id,
        SUM(CASE WHEN product_id IS NULL THEN 1 ELSE 0 END) as null_product_id
    FROM {{ params.database }}.{{ params.schema }}.raw_pos
    WHERE load_timestamp >= CURRENT_TIMESTAMP() - INTERVAL '2 hours'
    
    UNION ALL
    
    SELECT 
        'raw_orders' as table_name,
        COUNT(*) as total_rows,
        SUM(CASE WHEN order_id IS NULL THEN 1 ELSE 0 END) as null_transaction_id,
        SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) as null_store_id,
        0 as null_product_id
    FROM {{ params.database }}.{{ params.schema }}.raw_orders
    WHERE load_timestamp >= CURRENT_TIMESTAMP() - INTERVAL '2 hours'
    """,
    params={
        'database': SNOWFLAKE_DATABASE,
        'schema': SNOWFLAKE_SCHEMA,
    },
    dag=dag,
)

# Task: Send notification on success
send_success_notification = BashOperator(
    task_id='send_success_notification',
    bash_command='echo "Ingestion pipeline completed successfully"',
    dag=dag,
)

# Task dependencies
check_pipes >> validate_ingestion_task >> data_quality_checks >> send_success_notification


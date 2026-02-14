"""
Airflow DAG for loading dimension tables into Synapse Analytics.
Handles SCD Type 1 and Type 2 logic.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.microsoft.azure.operators.synapse import AzureSynapseRunSparkBatchOperator
from airflow.providers.microsoft.azure.sensors.synapse import AzureSynapseSparkBatchSensor
from airflow.providers.microsoft.azure.hooks.synapse import AzureSynapseHook
from airflow.operators.python import PythonOperator
from airflow.operators.sql import SQLExecuteQueryOperator

default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
    'email': ['data-engineering-team@company.com']
}

with DAG(
    'load_dimensions_synapse',
    default_args=default_args,
    description='Load dimension tables to Synapse with SCD logic',
    schedule_interval='0 5 * * *',  # Daily at 5 AM
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['warehouse', 'dimensions', 'scd', 'synapse'],
) as dag:

    # Load Customer Dimension (SCD Type 2)
    load_customer_dim = SQLExecuteQueryOperator(
        task_id='load_customer_dimension_scd2',
        conn_id='synapse_sql_pool',
        sql='EXEC dwh.sp_load_customer_dimension @processing_date = {{ ds }}',
    )

    # Load Product Dimension (SCD Type 1)
    load_product_dim = SQLExecuteQueryOperator(
        task_id='load_product_dimension_scd1',
        conn_id='synapse_sql_pool',
        sql='EXEC dwh.sp_load_product_dimension @processing_date = {{ ds }}',
    )

    # Load Store Dimension (SCD Type 2)
    load_store_dim = SQLExecuteQueryOperator(
        task_id='load_store_dimension_scd2',
        conn_id='synapse_sql_pool',
        sql='EXEC dwh.sp_load_store_dimension @processing_date = {{ ds }}',
    )

    # Load Geography Dimension (SCD Type 2)
    load_geography_dim = SQLExecuteQueryOperator(
        task_id='load_geography_dimension_scd2',
        conn_id='synapse_sql_pool',
        sql='EXEC dwh.sp_load_geography_dimension @processing_date = {{ ds }}',
    )

    # Load Date Dimension (static, one-time load)
    load_date_dim = SQLExecuteQueryOperator(
        task_id='load_date_dimension',
        conn_id='synapse_sql_pool',
        sql='EXEC dwh.sp_load_date_dimension',
    )

    # Validate dimension loads
    validate_dimensions = SQLExecuteQueryOperator(
        task_id='validate_dimension_loads',
        conn_id='synapse_sql_pool',
        sql='EXEC dwh.sp_validate_dimensions',
    )

    # Set dependencies - load dimensions in parallel, then validate
    [load_customer_dim, load_product_dim, load_store_dim, load_geography_dim, load_date_dim] >> validate_dimensions


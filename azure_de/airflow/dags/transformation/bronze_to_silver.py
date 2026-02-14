"""
Airflow DAG for transforming data from Bronze (raw) to Silver (staging) layer.
Applies cleaning, validation, and standardization.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.microsoft.azure.operators.databricks import DatabricksSubmitRunOperator
from airflow.providers.microsoft.azure.sensors.databricks import DatabricksRunStateSensor
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup

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
    'transform_bronze_to_silver',
    default_args=default_args,
    description='Transform data from Bronze to Silver layer',
    schedule_interval='0 3 * * *',  # Daily at 3 AM
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['transformation', 'bronze', 'silver', 'databricks'],
) as dag:

    # Task group for POS events transformation
    with TaskGroup('pos_events_transformation') as pos_group:
        transform_pos_events = DatabricksSubmitRunOperator(
            task_id='transform_pos_events',
            databricks_conn_id='databricks_default',
            existing_cluster_id='{{ var.value.databricks_cluster_id }}',
            notebook_task={
                'notebook_path': '/Shared/transformation/bronze_to_silver_pos',
                'base_parameters': {
                    'bronze_path': 'abfss://bronze@{{ var.value.adls_storage_account }}.dfs.core.windows.net/pos/events/',
                    'silver_path': 'abfss://silver@{{ var.value.adls_storage_account }}.dfs.core.windows.net/pos/events/',
                    'processing_date': '{{ ds }}',
                }
            },
        )

    # Task group for orders transformation
    with TaskGroup('orders_transformation') as orders_group:
        transform_orders = DatabricksSubmitRunOperator(
            task_id='transform_orders',
            databricks_conn_id='databricks_default',
            existing_cluster_id='{{ var.value.databricks_cluster_id }}',
            notebook_task={
                'notebook_path': '/Shared/transformation/bronze_to_silver_orders',
                'base_parameters': {
                    'bronze_path': 'abfss://bronze@{{ var.value.adls_storage_account }}.dfs.core.windows.net/orders/',
                    'silver_path': 'abfss://silver@{{ var.value.adls_storage_account }}.dfs.core.windows.net/orders/',
                    'processing_date': '{{ ds }}',
                }
            },
        )

    # Task group for rewards transformation
    with TaskGroup('rewards_transformation') as rewards_group:
        transform_rewards = DatabricksSubmitRunOperator(
            task_id='transform_rewards',
            databricks_conn_id='databricks_default',
            existing_cluster_id='{{ var.value.databricks_cluster_id }}',
            notebook_task={
                'notebook_path': '/Shared/transformation/bronze_to_silver_rewards',
                'base_parameters': {
                    'bronze_path': 'abfss://bronze@{{ var.value.adls_storage_account }}.dfs.core.windows.net/rewards/',
                    'silver_path': 'abfss://silver@{{ var.value.adls_storage_account }}.dfs.core.windows.net/rewards/',
                    'processing_date': '{{ ds }}',
                }
            },
        )

    # Data quality checks on Silver layer
    quality_check_silver = DatabricksSubmitRunOperator(
        task_id='quality_check_silver',
        databricks_conn_id='databricks_default',
        existing_cluster_id='{{ var.value.databricks_cluster_id }}',
        notebook_task={
            'notebook_path': '/Shared/quality/validate_silver_layer',
            'base_parameters': {
                'silver_path': 'abfss://silver@{{ var.value.adls_storage_account }}.dfs.core.windows.net/',
                'processing_date': '{{ ds }}',
            }
        },
    )

    # Set dependencies - run transformations in parallel, then quality check
    [pos_group, orders_group, rewards_group] >> quality_check_silver


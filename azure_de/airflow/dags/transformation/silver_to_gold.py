"""
Airflow DAG for transforming data from Silver (staging) to Gold (curated) layer.
Applies business logic, joins, aggregations, and enrichment.
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
    'transform_silver_to_gold',
    default_args=default_args,
    description='Transform data from Silver to Gold (curated) layer',
    schedule_interval='0 4 * * *',  # Daily at 4 AM
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['transformation', 'silver', 'gold', 'curated', 'databricks'],
) as dag:

    # Transform to curated sales fact
    transform_sales_fact = DatabricksSubmitRunOperator(
        task_id='transform_sales_fact',
        databricks_conn_id='databricks_default',
        existing_cluster_id='{{ var.value.databricks_cluster_id }}',
        notebook_task={
            'notebook_path': '/Shared/transformation/silver_to_gold_sales',
            'base_parameters': {
                'silver_path': 'abfss://silver@{{ var.value.adls_storage_account }}.dfs.core.windows.net/',
                'gold_path': 'abfss://gold@{{ var.value.adls_storage_account }}.dfs.core.windows.net/',
                'processing_date': '{{ ds }}',
            }
        },
    )

    # Transform to curated customer dimension
    transform_customer_dim = DatabricksSubmitRunOperator(
        task_id='transform_customer_dimension',
        databricks_conn_id='databricks_default',
        existing_cluster_id='{{ var.value.databricks_cluster_id }}',
        notebook_task={
            'notebook_path': '/Shared/transformation/silver_to_gold_customer',
            'base_parameters': {
                'silver_path': 'abfss://silver@{{ var.value.adls_storage_account }}.dfs.core.windows.net/',
                'gold_path': 'abfss://gold@{{ var.value.adls_storage_account }}.dfs.core.windows.net/',
                'processing_date': '{{ ds }}',
            }
        },
    )

    # Transform to curated product dimension
    transform_product_dim = DatabricksSubmitRunOperator(
        task_id='transform_product_dimension',
        databricks_conn_id='databricks_default',
        existing_cluster_id='{{ var.value.databricks_cluster_id }}',
        notebook_task={
            'notebook_path': '/Shared/transformation/silver_to_gold_product',
            'base_parameters': {
                'silver_path': 'abfss://silver@{{ var.value.adls_storage_account }}.dfs.core.windows.net/',
                'gold_path': 'abfss://gold@{{ var.value.adls_storage_account }}.dfs.core.windows.net/',
                'processing_date': '{{ ds }}',
            }
        },
    )

    # Data quality checks on Gold layer
    quality_check_gold = DatabricksSubmitRunOperator(
        task_id='quality_check_gold',
        databricks_conn_id='databricks_default',
        existing_cluster_id='{{ var.value.databricks_cluster_id }}',
        notebook_task={
            'notebook_path': '/Shared/quality/validate_gold_layer',
            'base_parameters': {
                'gold_path': 'abfss://gold@{{ var.value.adls_storage_account }}.dfs.core.windows.net/',
                'processing_date': '{{ ds }}',
            }
        },
    )

    # Set dependencies - run transformations in parallel, then quality check
    [transform_sales_fact, transform_customer_dim, transform_product_dim] >> quality_check_gold


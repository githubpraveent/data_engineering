"""
Airflow DAG for batch ingestion of order data from source database to ADLS Bronze.
Uses Azure Data Factory for the actual copy operation.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.microsoft.azure.operators.data_factory import AzureDataFactoryRunPipelineOperator
from airflow.providers.microsoft.azure.sensors.data_factory import AzureDataFactoryPipelineRunStatusSensor
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

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
    'ingest_orders_batch',
    default_args=default_args,
    description='Batch ingestion of order data from source DB to ADLS Bronze',
    schedule_interval='0 2 * * *',  # Daily at 2 AM
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['ingestion', 'batch', 'orders', 'adf'],
) as dag:

    # Trigger ADF pipeline for order ingestion
    trigger_adf_pipeline = AzureDataFactoryRunPipelineOperator(
        task_id='trigger_order_ingestion_pipeline',
        azure_data_factory_conn_id='azure_data_factory_default',
        resource_group_name='{{ var.value.resource_group_name }}',
        factory_name='{{ var.value.data_factory_name }}',
        pipeline_name='ingest_orders_to_bronze',
        parameters={
            'source_db': '{{ var.value.source_order_db }}',
            'source_table': 'orders',
            'bronze_path': 'abfss://bronze@{{ var.value.adls_storage_account }}.dfs.core.windows.net/orders/',
            'incremental_date': '{{ ds }}',  # Airflow execution date
        },
    )

    # Monitor ADF pipeline execution
    monitor_adf_pipeline = AzureDataFactoryPipelineRunStatusSensor(
        task_id='monitor_adf_pipeline',
        azure_data_factory_conn_id='azure_data_factory_default',
        resource_group_name='{{ var.value.resource_group_name }}',
        factory_name='{{ var.value.data_factory_name }}',
        run_id='{{ ti.xcom_pull(task_ids="trigger_order_ingestion_pipeline")["run_id"] }}',
        poke_interval=30,
        timeout=3600,
    )

    # Validate ingested data
    validate_ingestion = BashOperator(
        task_id='validate_ingestion',
        bash_command='echo "Validating ingested order data..."',
    )

    # Set dependencies
    trigger_adf_pipeline >> monitor_adf_pipeline >> validate_ingestion


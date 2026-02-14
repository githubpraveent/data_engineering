"""
Airflow DAG for CDC (Change Data Capture) from rewards database.
Extracts only changed records and loads to ADLS Bronze.
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
    'ingest_rewards_cdc',
    default_args=default_args,
    description='CDC ingestion from rewards database to ADLS Bronze',
    schedule_interval='0 */4 * * *',  # Every 4 hours
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['ingestion', 'cdc', 'rewards', 'incremental'],
) as dag:

    # Get last CDC timestamp
    get_last_cdc_timestamp = PythonOperator(
        task_id='get_last_cdc_timestamp',
        python_callable=lambda: None,  # Placeholder - implement logic to get last CDC timestamp
    )

    # Trigger ADF CDC pipeline
    trigger_cdc_pipeline = AzureDataFactoryRunPipelineOperator(
        task_id='trigger_cdc_pipeline',
        azure_data_factory_conn_id='azure_data_factory_default',
        resource_group_name='{{ var.value.resource_group_name }}',
        factory_name='{{ var.value.data_factory_name }}',
        pipeline_name='cdc_rewards_to_bronze',
        parameters={
            'source_db': '{{ var.value.source_rewards_db }}',
            'bronze_path': 'abfss://bronze@{{ var.value.adls_storage_account }}.dfs.core.windows.net/rewards/',
            'last_cdc_timestamp': '{{ ti.xcom_pull(task_ids="get_last_cdc_timestamp") }}',
        },
    )

    # Monitor CDC pipeline
    monitor_cdc_pipeline = AzureDataFactoryPipelineRunStatusSensor(
        task_id='monitor_cdc_pipeline',
        azure_data_factory_conn_id='azure_data_factory_default',
        resource_group_name='{{ var.value.resource_group_name }}',
        factory_name='{{ var.value.data_factory_name }}',
        run_id='{{ ti.xcom_pull(task_ids="trigger_cdc_pipeline")["run_id"] }}',
        poke_interval=30,
        timeout=1800,
    )

    # Update CDC timestamp
    update_cdc_timestamp = PythonOperator(
        task_id='update_cdc_timestamp',
        python_callable=lambda: None,  # Placeholder - implement logic to update CDC timestamp
    )

    # Set dependencies
    get_last_cdc_timestamp >> trigger_cdc_pipeline >> monitor_cdc_pipeline >> update_cdc_timestamp


"""
Airflow DAG for streaming POS events from Event Hubs to ADLS Bronze layer.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.microsoft.azure.operators.databricks import DatabricksSubmitRunOperator
from airflow.providers.microsoft.azure.sensors.databricks import DatabricksRunStateSensor
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.task_group import TaskGroup

default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'email': ['data-engineering-team@company.com']
}

with DAG(
    'ingest_pos_events_stream',
    default_args=default_args,
    description='Stream POS events from Event Hubs to ADLS Bronze',
    schedule_interval=timedelta(minutes=15),  # Run every 15 minutes
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['ingestion', 'streaming', 'pos', 'event-hubs'],
) as dag:

    # Task to check Event Hubs connectivity
    check_event_hubs = BashOperator(
        task_id='check_event_hubs_connectivity',
        bash_command='echo "Checking Event Hubs connectivity..."',
    )

    # Databricks job to stream from Event Hubs to Bronze
    stream_to_bronze = DatabricksSubmitRunOperator(
        task_id='stream_pos_events_to_bronze',
        databricks_conn_id='databricks_default',
        existing_cluster_id='{{ var.value.databricks_cluster_id }}',
        notebook_task={
            'notebook_path': '/Shared/ingestion/stream_pos_events_to_bronze',
            'base_parameters': {
                'event_hub_name': 'pos-events',
                'consumer_group': 'databricks-streaming',
                'bronze_path': 'abfss://bronze@{{ var.value.adls_storage_account }}.dfs.core.windows.net/pos/events/',
                'checkpoint_path': 'abfss://bronze@{{ var.value.adls_storage_account }}.dfs.core.windows.net/checkpoints/pos_events/',
            }
        },
    )

    # Monitor the streaming job
    monitor_streaming = DatabricksRunStateSensor(
        task_id='monitor_streaming_job',
        databricks_conn_id='databricks_default',
        run_id='{{ ti.xcom_pull(task_ids="stream_pos_events_to_bronze")["run_id"] }}',
        poke_interval=60,
        timeout=3600,
    )

    # Data quality check on ingested data
    quality_check = DatabricksSubmitRunOperator(
        task_id='quality_check_bronze_pos',
        databricks_conn_id='databricks_default',
        existing_cluster_id='{{ var.value.databricks_cluster_id }}',
        notebook_task={
            'notebook_path': '/Shared/quality/validate_bronze_ingestion',
            'base_parameters': {
                'source_path': 'abfss://bronze@{{ var.value.adls_storage_account }}.dfs.core.windows.net/pos/events/',
                'source_type': 'pos_events',
            }
        },
    )

    # Alert on failure
    send_alert = BashOperator(
        task_id='send_alert_on_failure',
        bash_command='echo "Alert: POS ingestion failed"',
        trigger_rule='one_failed',
    )

    # Set task dependencies
    check_event_hubs >> stream_to_bronze >> monitor_streaming >> quality_check
    quality_check >> send_alert


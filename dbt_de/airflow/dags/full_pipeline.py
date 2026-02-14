"""
Full pipeline DAG: Ingestion → Transformation → Quality Checks
Orchestrates the complete data pipeline end-to-end
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.models import Variable

# Default arguments
default_args = {
    'owner': 'data_engineering',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Create DAG
dag = DAG(
    'full_data_pipeline',
    default_args=default_args,
    description='End-to-end data pipeline: ingestion → transformation',
    schedule_interval='0 0 * * *',  # Daily at midnight
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['pipeline', 'orchestration', 'end-to-end'],
)

# Trigger ingestion DAG
trigger_ingestion = TriggerDagRunOperator(
    task_id='trigger_ingestion',
    trigger_dag_id='data_ingestion_bronze',
    wait_for_completion=True,
    poke_interval=60,  # Check every minute
    dag=dag,
)

# Trigger transformation DAG (depends on ingestion)
trigger_transformation = TriggerDagRunOperator(
    task_id='trigger_transformation',
    trigger_dag_id='dbt_retail_transformations',
    wait_for_completion=True,
    poke_interval=60,
    dag=dag,
)

# Define dependencies
trigger_ingestion >> trigger_transformation


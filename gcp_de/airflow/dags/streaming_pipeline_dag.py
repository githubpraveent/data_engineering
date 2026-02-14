"""
Streaming Pipeline DAG
Monitors and manages Dataflow streaming jobs that consume from Pub/Sub.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.google.cloud.operators.dataflow import (
    DataflowStartStreamingPipelineOperator,
    DataflowStopPipelineOperator
)
from airflow.providers.google.cloud.sensors.dataflow import DataflowJobStatusSensor
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import os

default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'start_date': days_ago(1),
}

PROJECT_ID = os.environ.get('GCP_PROJECT', 'your-project-id')
REGION = os.environ.get('REGION', 'us-central1')
DATAFLOW_STAGING = os.environ.get('DATAFLOW_STAGING', f'{PROJECT_ID}-dataflow-staging-dev')
DATAFLOW_TEMP = os.environ.get('DATAFLOW_TEMP', f'{PROJECT_ID}-dataflow-temp-dev')
RAW_BUCKET = os.environ.get('RAW_BUCKET', f'{PROJECT_ID}-data-lake-raw-dev')
STAGING_DATASET = os.environ.get('STAGING_DATASET', 'staging_dev')

# Pub/Sub topics
TRANSACTIONS_TOPIC = f'retail-transactions-{os.environ.get("ENVIRONMENT", "dev")}'
INVENTORY_TOPIC = f'retail-inventory-{os.environ.get("ENVIRONMENT", "dev")}'
CUSTOMERS_TOPIC = f'retail-customers-{os.environ.get("ENVIRONMENT", "dev")}'

# Streaming pipeline template
STREAMING_TEMPLATE = f'gs://{DATAFLOW_STAGING}/templates/streaming_pipeline_template'

with DAG(
    'streaming_pipeline_monitor',
    default_args=default_args,
    description='Monitor and manage streaming Dataflow pipelines',
    schedule_interval='*/10 * * * *',  # Every 10 minutes
    catchup=False,
    max_active_runs=1,
    tags=['streaming', 'pubsub', 'dataflow'],
) as dag:

    def check_streaming_job_health(**context):
        """
        Check if streaming jobs are running and healthy.
        This is a placeholder - in production, you'd query Dataflow API.
        """
        from google.cloud import dataflow_v1beta3
        
        client = dataflow_v1beta3.JobsV1Beta3Client()
        project_id = PROJECT_ID
        location = REGION
        
        # List active streaming jobs
        request = dataflow_v1beta3.ListJobsRequest(
            project_id=project_id,
            location=location,
            filter=dataflow_v1beta3.ListJobsRequest.Filter.ACTIVE,
        )
        
        jobs = client.list_jobs(request=request)
        streaming_jobs = [job for job in jobs.jobs if job.type == dataflow_v1beta3.JobType.JOB_TYPE_STREAMING]
        
        if not streaming_jobs:
            raise ValueError("No active streaming jobs found!")
        
        print(f"Found {len(streaming_jobs)} active streaming jobs")
        for job in streaming_jobs:
            print(f"Job: {job.name}, State: {job.current_state}")
        
        return len(streaming_jobs)

    # Task 1: Check streaming job health
    check_job_health = PythonOperator(
        task_id='check_streaming_job_health',
        python_callable=check_streaming_job_health,
    )

    # Task 2: Monitor transactions streaming job
    monitor_transactions_job = DataflowJobStatusSensor(
        task_id='monitor_transactions_job',
        job_name='streaming-transactions-pipeline',
        location=REGION,
        project_id=PROJECT_ID,
        expected_statuses=['JOB_STATE_RUNNING'],
        timeout=300,
    )

    # Note: In production, you would typically:
    # 1. Deploy streaming jobs separately (they run continuously)
    # 2. Use this DAG only for monitoring and alerting
    # 3. Use DataflowStartStreamingPipelineOperator to start jobs if needed
    # 4. Use DataflowStopPipelineOperator to gracefully stop jobs for maintenance


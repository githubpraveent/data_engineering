"""
Batch ETL DAG
Orchestrates the full batch data pipeline from GCS landing to BigQuery curated tables.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.google.cloud.operators.gcs import GCSListObjectsOperator
from airflow.providers.google.cloud.sensors.gcs import GCSObjectsWithPrefixExistenceSensor
from airflow.providers.google.cloud.operators.dataflow import DataflowTemplatedJobStartOperator
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryInsertJobOperator,
    BigQueryCheckOperator
)
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import os

# Default arguments
default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': days_ago(1),
}

# Environment variables
PROJECT_ID = os.environ.get('GCP_PROJECT', 'your-project-id')
REGION = os.environ.get('REGION', 'us-central1')
RAW_BUCKET = os.environ.get('RAW_BUCKET', f'{PROJECT_ID}-data-lake-raw-dev')
STAGING_BUCKET = os.environ.get('STAGING_BUCKET', f'{PROJECT_ID}-data-lake-staging-dev')
CURATED_BUCKET = os.environ.get('CURATED_BUCKET', f'{PROJECT_ID}-data-lake-curated-dev')
DATAFLOW_STAGING = os.environ.get('DATAFLOW_STAGING', f'{PROJECT_ID}-dataflow-staging-dev')
DATAFLOW_TEMP = os.environ.get('DATAFLOW_TEMP', f'{PROJECT_ID}-dataflow-temp-dev')
STAGING_DATASET = os.environ.get('STAGING_DATASET', 'staging_dev')
CURATED_DATASET = os.environ.get('CURATED_DATASET', 'curated_dev')

# Dataflow template paths (update with your actual template locations)
BATCH_TRANSFORM_TEMPLATE = f'gs://{DATAFLOW_STAGING}/templates/batch_transform_template'
BATCH_LOAD_TEMPLATE = f'gs://{DATAFLOW_STAGING}/templates/batch_load_template'

with DAG(
    'batch_etl_pipeline',
    default_args=default_args,
    description='Batch ETL pipeline from GCS to BigQuery',
    schedule_interval='0 2 * * *',  # Daily at 2 AM UTC
    catchup=False,
    max_active_runs=1,
    tags=['batch', 'etl', 'gcs', 'bigquery'],
) as dag:

    # Task 1: Check for new files in raw bucket
    check_raw_files = GCSObjectsWithPrefixExistenceSensor(
        task_id='check_raw_files',
        bucket=RAW_BUCKET,
        prefix='transactions/',
        poke_interval=60,
        timeout=600,
    )

    # Task 2: List files in raw bucket (for logging)
    list_raw_files = GCSListObjectsOperator(
        task_id='list_raw_files',
        bucket=RAW_BUCKET,
        prefix='transactions/',
    )

    # Task 3: Transform data from raw to staging (Dataflow)
    transform_raw_to_staging = DataflowTemplatedJobStartOperator(
        task_id='transform_raw_to_staging',
        template=BATCH_TRANSFORM_TEMPLATE,
        location=REGION,
        job_name='batch-transform-{{ ds_nodash }}-{{ ts_nodash }}',
        parameters={
            'input': f'gs://{RAW_BUCKET}/transactions/',
            'output': f'gs://{STAGING_BUCKET}/transactions/',
            'temp_location': f'gs://{DATAFLOW_TEMP}/',
            'staging_location': f'gs://{DATAFLOW_STAGING}/',
        },
        project_id=PROJECT_ID,
    )

    # Task 4: Data quality check on staging data
    validate_staging_data = BigQueryCheckOperator(
        task_id='validate_staging_data',
        sql=f"""
        SELECT COUNT(*) as row_count
        FROM `{PROJECT_ID}.{STAGING_DATASET}.transactions_staging`
        WHERE DATE(transaction_timestamp) = DATE('{{{{ ds }}}}')
        """,
        use_legacy_sql=False,
    )

    # Task 5: Load staging data to BigQuery curated tables
    load_to_curated = DataflowTemplatedJobStartOperator(
        task_id='load_to_curated',
        template=BATCH_LOAD_TEMPLATE,
        location=REGION,
        job_name='batch-load-{{ ds_nodash }}-{{ ts_nodash }}',
        parameters={
            'input': f'gs://{STAGING_BUCKET}/transactions/',
            'output_table': f'{PROJECT_ID}:{CURATED_DATASET}.transactions',
            'temp_location': f'gs://{DATAFLOW_TEMP}/',
            'staging_location': f'gs://{DATAFLOW_STAGING}/',
        },
        project_id=PROJECT_ID,
    )

    # Task 6: Run data quality checks on curated data
    validate_curated_data = BigQueryCheckOperator(
        task_id='validate_curated_data',
        sql=f"""
        SELECT 
            COUNT(*) as row_count,
            COUNT(DISTINCT transaction_id) as unique_transactions,
            SUM(total_amount) as total_revenue
        FROM `{PROJECT_ID}.{CURATED_DATASET}.transactions`
        WHERE DATE(transaction_timestamp) = DATE('{{{{ ds }}}}')
        HAVING row_count > 0 AND unique_transactions = row_count
        """,
        use_legacy_sql=False,
    )

    # Task 7: Update fact tables
    update_sales_fact = BigQueryInsertJobOperator(
        task_id='update_sales_fact',
        configuration={
            'query': {
                'query': f"""
                INSERT INTO `{PROJECT_ID}.{CURATED_DATASET}.sales_fact`
                SELECT 
                    transaction_id,
                    customer_id,
                    product_id,
                    store_id,
                    transaction_timestamp,
                    quantity,
                    unit_price,
                    total_amount,
                    payment_method,
                    CURRENT_TIMESTAMP() as load_timestamp
                FROM `{PROJECT_ID}.{CURATED_DATASET}.transactions`
                WHERE DATE(transaction_timestamp) = DATE('{{{{ ds }}}}')
                """,
                'useLegacySql': False,
                'writeDisposition': 'WRITE_APPEND',
            }
        },
        project_id=PROJECT_ID,
    )

    # Task 8: Generate daily summary
    generate_daily_summary = BigQueryInsertJobOperator(
        task_id='generate_daily_summary',
        configuration={
            'query': {
                'query': f"""
                CREATE OR REPLACE TABLE `{PROJECT_ID}.{CURATED_DATASET}.daily_sales_summary`
                PARTITION BY transaction_date
                AS
                SELECT 
                    DATE(transaction_timestamp) as transaction_date,
                    COUNT(DISTINCT transaction_id) as total_transactions,
                    COUNT(DISTINCT customer_id) as unique_customers,
                    SUM(total_amount) as total_revenue,
                    AVG(total_amount) as avg_transaction_value,
                    COUNT(DISTINCT product_id) as unique_products,
                    CURRENT_TIMESTAMP() as last_updated
                FROM `{PROJECT_ID}.{CURATED_DATASET}.sales_fact`
                WHERE DATE(transaction_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
                GROUP BY transaction_date
                """,
                'useLegacySql': False,
            }
        },
        project_id=PROJECT_ID,
    )

    # Define task dependencies
    check_raw_files >> list_raw_files >> transform_raw_to_staging
    transform_raw_to_staging >> validate_staging_data
    validate_staging_data >> load_to_curated
    load_to_curated >> validate_curated_data
    validate_curated_data >> update_sales_fact
    update_sales_fact >> generate_daily_summary


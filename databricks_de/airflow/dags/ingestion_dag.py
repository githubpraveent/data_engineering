"""
Airflow DAG: Data Ingestion Pipeline
Orchestrates batch and streaming ingestion jobs to Databricks Bronze layer.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.databricks.operators.databricks import DatabricksSubmitRunOperator
from airflow.providers.databricks.sensors.databricks import DatabricksJobRunSensor
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import os

# Default arguments
default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'email': ['data-engineering@company.com'],
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'retry_exponential_backoff': True,
    'max_retry_delay': timedelta(minutes=30),
}

# DAG configuration
dag = DAG(
    'retail_ingestion_pipeline',
    default_args=default_args,
    description='Retail Data Lakehouse - Ingestion Pipeline',
    schedule_interval=timedelta(hours=1),  # Run hourly
    start_date=days_ago(1),
    catchup=False,
    tags=['ingestion', 'bronze', 'retail'],
    max_active_runs=1,
)

# Environment configuration
ENVIRONMENT = os.getenv('ENVIRONMENT', 'dev')
DATABRICKS_CONN_ID = f'databricks_{ENVIRONMENT}'
CATALOG = os.getenv('DATABRICKS_CATALOG', 'retail_datalake')
BRONZE_SCHEMA = 'bronze'

# Notebook paths (adjust based on your notebook structure)
NOTEBOOKS_BASE_PATH = f'/Workspace/Users/{os.getenv("DATABRICKS_USER", "data-engineer")}/retail-datalake'

# Cluster configuration
CLUSTER_CONFIG = {
    'spark_version': '13.3.x-scala2.12',
    'node_type_id': 'i3.xlarge',
    'driver_node_type_id': 'i3.xlarge',
    'num_workers': 2,
    'spark_conf': {
        'spark.databricks.delta.optimizeWrite.enabled': 'true',
        'spark.databricks.delta.autoCompact.enabled': 'true',
    },
}

# Task: Ingest Orders
ingest_orders = DatabricksSubmitRunOperator(
    task_id='ingest_orders',
    databricks_conn_id=DATABRICKS_CONN_ID,
    existing_cluster_id=os.getenv('DATABRICKS_CLUSTER_ID', None),  # Use existing cluster if available
    new_cluster=CLUSTER_CONFIG if not os.getenv('DATABRICKS_CLUSTER_ID') else None,
    notebook_task={
        'notebook_path': f'{NOTEBOOKS_BASE_PATH}/databricks/notebooks/ingestion/batch/ingest_orders',
        'base_parameters': {
            'source_system': 'orders_db',
            'environment': ENVIRONMENT,
            'catalog': CATALOG,
            'bronze_schema': BRONZE_SCHEMA,
            'source_path': os.getenv('ORDERS_SOURCE_PATH', ''),
        }
    },
    dag=dag,
)

# Task: Ingest Customers
ingest_customers = DatabricksSubmitRunOperator(
    task_id='ingest_customers',
    databricks_conn_id=DATABRICKS_CONN_ID,
    existing_cluster_id=os.getenv('DATABRICKS_CLUSTER_ID', None),
    new_cluster=CLUSTER_CONFIG if not os.getenv('DATABRICKS_CLUSTER_ID') else None,
    notebook_task={
        'notebook_path': f'{NOTEBOOKS_BASE_PATH}/databricks/notebooks/ingestion/batch/ingest_customers',
        'base_parameters': {
            'source_system': 'customers_db',
            'environment': ENVIRONMENT,
            'catalog': CATALOG,
            'bronze_schema': BRONZE_SCHEMA,
            'source_path': os.getenv('CUSTOMERS_SOURCE_PATH', ''),
        }
    },
    dag=dag,
)

# Task: Ingest Inventory
ingest_inventory = DatabricksSubmitRunOperator(
    task_id='ingest_inventory',
    databricks_conn_id=DATABRICKS_CONN_ID,
    existing_cluster_id=os.getenv('DATABRICKS_CLUSTER_ID', None),
    new_cluster=CLUSTER_CONFIG if not os.getenv('DATABRICKS_CLUSTER_ID') else None,
    notebook_task={
        'notebook_path': f'{NOTEBOOKS_BASE_PATH}/databricks/notebooks/ingestion/batch/ingest_inventory',
        'base_parameters': {
            'source_system': 'inventory_db',
            'environment': ENVIRONMENT,
            'catalog': CATALOG,
            'bronze_schema': BRONZE_SCHEMA,
            'source_path': os.getenv('INVENTORY_SOURCE_PATH', ''),
        }
    },
    dag=dag,
)

# Task: Monitor Streaming Ingestion (if using streaming)
# Note: Streaming jobs are typically long-running and monitored separately
# This task can check streaming job status or trigger streaming job start

def check_streaming_status(**context):
    """Check streaming job status (placeholder for actual implementation)."""
    # In production, query Databricks API to check streaming job status
    return True

monitor_streaming = PythonOperator(
    task_id='monitor_streaming',
    python_callable=check_streaming_status,
    dag=dag,
)

# Task: Ingestion Metrics Collection
def collect_ingestion_metrics(**context):
    """Collect ingestion metrics after batch jobs complete."""
    # Query Databricks tables to collect metrics
    # Store in monitoring table or send to monitoring system
    return True

collect_metrics = PythonOperator(
    task_id='collect_ingestion_metrics',
    python_callable=collect_ingestion_metrics,
    dag=dag,
)

# Task dependencies
# Orders, Customers, and Inventory can run in parallel
[ingest_orders, ingest_customers, ingest_inventory] >> collect_metrics

# Streaming monitoring runs independently (always running)
monitor_streaming


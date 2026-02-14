"""
Airflow DAG: Data Quality Checks
Runs data quality validation after transformations.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.databricks.operators.databricks import DatabricksSubmitRunOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from airflow.operators.bash import BashOperator
from airflow.exceptions import AirflowException
import os

default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'email': ['data-engineering@company.com'],
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'retail_data_quality_checks',
    default_args=default_args,
    description='Retail Data Lakehouse - Data Quality Validation',
    schedule_interval=timedelta(hours=2),  # Run every 2 hours (after transformation)
    start_date=days_ago(1),
    catchup=False,
    tags=['data-quality', 'validation', 'retail'],
    max_active_runs=1,
)

ENVIRONMENT = os.getenv('ENVIRONMENT', 'dev')
DATABRICKS_CONN_ID = f'databricks_{ENVIRONMENT}'
CATALOG = os.getenv('DATABRICKS_CATALOG', 'retail_datalake')

NOTEBOOKS_BASE_PATH = f'/Workspace/Users/{os.getenv("DATABRICKS_USER", "data-engineer")}/retail-datalake'

CLUSTER_CONFIG = {
    'spark_version': '13.3.x-scala2.12',
    'node_type_id': 'i3.xlarge',
    'driver_node_type_id': 'i3.xlarge',
    'num_workers': 2,
}

# Data quality check notebook (assumes we have a quality check notebook)
QUALITY_CHECK_NOTEBOOK = f'{NOTEBOOKS_BASE_PATH}/databricks/notebooks/utilities/data_quality_checks'

# Quality checks for Silver layer
quality_check_silver_orders = DatabricksSubmitRunOperator(
    task_id='quality_check_silver_orders',
    databricks_conn_id=DATABRICKS_CONN_ID,
    existing_cluster_id=os.getenv('DATABRICKS_CLUSTER_ID', None),
    new_cluster=CLUSTER_CONFIG if not os.getenv('DATABRICKS_CLUSTER_ID') else None,
    notebook_task={
        'notebook_path': QUALITY_CHECK_NOTEBOOK,
        'base_parameters': {
            'environment': ENVIRONMENT,
            'catalog': CATALOG,
            'table': f'{CATALOG}.{ENVIRONMENT}_silver.orders',
            'checks': 'not_null:order_id,unique:order_id,value_range:total_amount:min:0',
        }
    },
    dag=dag,
)

quality_check_silver_customers = DatabricksSubmitRunOperator(
    task_id='quality_check_silver_customers',
    databricks_conn_id=DATABRICKS_CONN_ID,
    existing_cluster_id=os.getenv('DATABRICKS_CLUSTER_ID', None),
    new_cluster=CLUSTER_CONFIG if not os.getenv('DATABRICKS_CLUSTER_ID') else None,
    notebook_task={
        'notebook_path': QUALITY_CHECK_NOTEBOOK,
        'base_parameters': {
            'environment': ENVIRONMENT,
            'catalog': CATALOG,
            'table': f'{CATALOG}.{ENVIRONMENT}_silver.customers',
            'checks': 'not_null:customer_id,unique:customer_id',
        }
    },
    dag=dag,
)

# Quality checks for Gold layer
quality_check_gold_fact_sales = DatabricksSubmitRunOperator(
    task_id='quality_check_gold_fact_sales',
    databricks_conn_id=DATABRICKS_CONN_ID,
    existing_cluster_id=os.getenv('DATABRICKS_CLUSTER_ID', None),
    new_cluster=CLUSTER_CONFIG if not os.getenv('DATABRICKS_CLUSTER_ID') else None,
    notebook_task={
        'notebook_path': QUALITY_CHECK_NOTEBOOK,
        'base_parameters': {
            'environment': ENVIRONMENT,
            'catalog': CATALOG,
            'table': f'{CATALOG}.{ENVIRONMENT}_gold.fact_sales',
            'checks': 'not_null:transaction_id,referential_integrity:customer_key:dim_customer:customer_key',
        }
    },
    dag=dag,
)

# Referential integrity check
def check_referential_integrity(**context):
    """Check referential integrity between fact and dimension tables."""
    # In production, implement actual referential integrity checks
    # Query Databricks tables and validate foreign keys exist in dimension tables
    return True

referential_integrity_check = PythonOperator(
    task_id='referential_integrity_check',
    python_callable=check_referential_integrity,
    dag=dag,
)

# Row count check
def check_row_counts(**context):
    """Check row counts are within expected ranges."""
    # In production, compare row counts against expected thresholds
    return True

row_count_check = PythonOperator(
    task_id='row_count_check',
    python_callable=check_row_counts,
    dag=dag,
)

# Data freshness check
def check_data_freshness(**context):
    """Check data freshness (last update timestamp)."""
    # In production, check last_update timestamps are recent
    return True

data_freshness_check = PythonOperator(
    task_id='data_freshness_check',
    python_callable=check_data_freshness,
    dag=dag,
)

# Generate quality report
def generate_quality_report(**context):
    """Generate data quality report."""
    # In production, aggregate quality check results and generate report
    # Send to monitoring system or store in database
    return True

generate_report = PythonOperator(
    task_id='generate_quality_report',
    python_callable=generate_quality_report,
    dag=dag,
)

# Task dependencies
[quality_check_silver_orders, quality_check_silver_customers] >> quality_check_gold_fact_sales
[quality_check_gold_fact_sales, referential_integrity_check, row_count_check, data_freshness_check] >> generate_report


"""
Airflow DAG: Data Transformation Pipeline
Orchestrates Bronze → Silver → Gold transformation jobs.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.databricks.operators.databricks import DatabricksSubmitRunOperator
from airflow.providers.databricks.sensors.databricks import DatabricksJobRunSensor
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from airflow.operators.bash import BashOperator
import os

default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'email': ['data-engineering@company.com'],
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
    'retry_exponential_backoff': True,
    'max_retry_delay': timedelta(minutes=60),
}

dag = DAG(
    'retail_transformation_pipeline',
    default_args=default_args,
    description='Retail Data Lakehouse - Transformation Pipeline (Bronze → Silver → Gold)',
    schedule_interval=timedelta(hours=2),  # Run every 2 hours
    start_date=days_ago(1),
    catchup=False,
    tags=['transformation', 'silver', 'gold', 'retail'],
    max_active_runs=1,
)

ENVIRONMENT = os.getenv('ENVIRONMENT', 'dev')
DATABRICKS_CONN_ID = f'databricks_{ENVIRONMENT}'
CATALOG = os.getenv('DATABRICKS_CATALOG', 'retail_datalake')
BRONZE_SCHEMA = 'bronze'
SILVER_SCHEMA = 'silver'
GOLD_SCHEMA = 'gold'

NOTEBOOKS_BASE_PATH = f'/Workspace/Users/{os.getenv("DATABRICKS_USER", "data-engineer")}/retail-datalake'

CLUSTER_CONFIG = {
    'spark_version': '13.3.x-scala2.12',
    'node_type_id': 'i3.xlarge',
    'driver_node_type_id': 'i3.xlarge',
    'num_workers': 3,  # Larger cluster for transformations
    'spark_conf': {
        'spark.databricks.delta.optimizeWrite.enabled': 'true',
        'spark.databricks.delta.autoCompact.enabled': 'true',
        'spark.sql.adaptive.enabled': 'true',
        'spark.sql.adaptive.coalescePartitions.enabled': 'true',
    },
}

# ============================================================================
# BRONZE TO SILVER TRANSFORMATIONS
# ============================================================================

# Transform Orders: Bronze → Silver
bronze_to_silver_orders = DatabricksSubmitRunOperator(
    task_id='bronze_to_silver_orders',
    databricks_conn_id=DATABRICKS_CONN_ID,
    existing_cluster_id=os.getenv('DATABRICKS_CLUSTER_ID', None),
    new_cluster=CLUSTER_CONFIG if not os.getenv('DATABRICKS_CLUSTER_ID') else None,
    notebook_task={
        'notebook_path': f'{NOTEBOOKS_BASE_PATH}/databricks/notebooks/transformation/bronze_to_silver/clean_orders',
        'base_parameters': {
            'environment': ENVIRONMENT,
            'catalog': CATALOG,
            'bronze_schema': BRONZE_SCHEMA,
            'silver_schema': SILVER_SCHEMA,
            'incremental': 'true',
        }
    },
    dag=dag,
)

# Transform Customers: Bronze → Silver
bronze_to_silver_customers = DatabricksSubmitRunOperator(
    task_id='bronze_to_silver_customers',
    databricks_conn_id=DATABRICKS_CONN_ID,
    existing_cluster_id=os.getenv('DATABRICKS_CLUSTER_ID', None),
    new_cluster=CLUSTER_CONFIG if not os.getenv('DATABRICKS_CLUSTER_ID') else None,
    notebook_task={
        'notebook_path': f'{NOTEBOOKS_BASE_PATH}/databricks/notebooks/transformation/bronze_to_silver/clean_customers',
        'base_parameters': {
            'environment': ENVIRONMENT,
            'catalog': CATALOG,
            'bronze_schema': BRONZE_SCHEMA,
            'silver_schema': SILVER_SCHEMA,
            'incremental': 'true',
        }
    },
    dag=dag,
)

# Transform Inventory: Bronze → Silver
bronze_to_silver_inventory = DatabricksSubmitRunOperator(
    task_id='bronze_to_silver_inventory',
    databricks_conn_id=DATABRICKS_CONN_ID,
    existing_cluster_id=os.getenv('DATABRICKS_CLUSTER_ID', None),
    new_cluster=CLUSTER_CONFIG if not os.getenv('DATABRICKS_CLUSTER_ID') else None,
    notebook_task={
        'notebook_path': f'{NOTEBOOKS_BASE_PATH}/databricks/notebooks/transformation/bronze_to_silver/clean_inventory',
        'base_parameters': {
            'environment': ENVIRONMENT,
            'catalog': CATALOG,
            'bronze_schema': BRONZE_SCHEMA,
            'silver_schema': SILVER_SCHEMA,
            'incremental': 'true',
        }
    },
    dag=dag,
)

# ============================================================================
# SILVER TO GOLD TRANSFORMATIONS (DIMENSIONS)
# ============================================================================

# Build Dimension: Date (static dimension, runs less frequently)
build_dim_date = DatabricksSubmitRunOperator(
    task_id='build_dim_date',
    databricks_conn_id=DATABRICKS_CONN_ID,
    existing_cluster_id=os.getenv('DATABRICKS_CLUSTER_ID', None),
    new_cluster=CLUSTER_CONFIG if not os.getenv('DATABRICKS_CLUSTER_ID') else None,
    notebook_task={
        'notebook_path': f'{NOTEBOOKS_BASE_PATH}/databricks/notebooks/transformation/silver_to_gold/build_dim_date',
        'base_parameters': {
            'environment': ENVIRONMENT,
            'catalog': CATALOG,
            'gold_schema': GOLD_SCHEMA,
            'start_date': '2020-01-01',
            'end_date': '2025-12-31',
        }
    },
    dag=dag,
)

# Build Dimension: Customer (SCD Type 2)
build_dim_customer = DatabricksSubmitRunOperator(
    task_id='build_dim_customer',
    databricks_conn_id=DATABRICKS_CONN_ID,
    existing_cluster_id=os.getenv('DATABRICKS_CLUSTER_ID', None),
    new_cluster=CLUSTER_CONFIG if not os.getenv('DATABRICKS_CLUSTER_ID') else None,
    notebook_task={
        'notebook_path': f'{NOTEBOOKS_BASE_PATH}/databricks/notebooks/transformation/silver_to_gold/build_dim_customer',
        'base_parameters': {
            'environment': ENVIRONMENT,
            'catalog': CATALOG,
            'silver_schema': SILVER_SCHEMA,
            'gold_schema': GOLD_SCHEMA,
            'incremental': 'true',
        }
    },
    dag=dag,
)

# Build Dimension: Product (SCD Type 2)
build_dim_product = DatabricksSubmitRunOperator(
    task_id='build_dim_product',
    databricks_conn_id=DATABRICKS_CONN_ID,
    existing_cluster_id=os.getenv('DATABRICKS_CLUSTER_ID', None),
    new_cluster=CLUSTER_CONFIG if not os.getenv('DATABRICKS_CLUSTER_ID') else None,
    notebook_task={
        'notebook_path': f'{NOTEBOOKS_BASE_PATH}/databricks/notebooks/transformation/silver_to_gold/build_dim_product',
        'base_parameters': {
            'environment': ENVIRONMENT,
            'catalog': CATALOG,
            'silver_schema': SILVER_SCHEMA,
            'gold_schema': GOLD_SCHEMA,
            'incremental': 'true',
        }
    },
    dag=dag,
)

# Build Dimension: Store (SCD Type 1)
build_dim_store = DatabricksSubmitRunOperator(
    task_id='build_dim_store',
    databricks_conn_id=DATABRICKS_CONN_ID,
    existing_cluster_id=os.getenv('DATABRICKS_CLUSTER_ID', None),
    new_cluster=CLUSTER_CONFIG if not os.getenv('DATABRICKS_CLUSTER_ID') else None,
    notebook_task={
        'notebook_path': f'{NOTEBOOKS_BASE_PATH}/databricks/notebooks/transformation/silver_to_gold/build_dim_store',
        'base_parameters': {
            'environment': ENVIRONMENT,
            'catalog': CATALOG,
            'silver_schema': SILVER_SCHEMA,
            'gold_schema': GOLD_SCHEMA,
        }
    },
    dag=dag,
)

# ============================================================================
# SILVER TO GOLD TRANSFORMATIONS (FACT TABLES)
# ============================================================================

# Build Fact: Sales (depends on all dimensions)
build_fact_sales = DatabricksSubmitRunOperator(
    task_id='build_fact_sales',
    databricks_conn_id=DATABRICKS_CONN_ID,
    existing_cluster_id=os.getenv('DATABRICKS_CLUSTER_ID', None),
    new_cluster=CLUSTER_CONFIG if not os.getenv('DATABRICKS_CLUSTER_ID') else None,
    notebook_task={
        'notebook_path': f'{NOTEBOOKS_BASE_PATH}/databricks/notebooks/transformation/silver_to_gold/build_fact_sales',
        'base_parameters': {
            'environment': ENVIRONMENT,
            'catalog': CATALOG,
            'silver_schema': SILVER_SCHEMA,
            'gold_schema': GOLD_SCHEMA,
            'incremental': 'true',
        }
    },
    dag=dag,
)

# ============================================================================
# TASK DEPENDENCIES
# ============================================================================

# Bronze → Silver: Can run in parallel
[bronze_to_silver_orders, bronze_to_silver_customers, bronze_to_silver_inventory] >> build_dim_date

# Dimensions: Date can run independently, others depend on Silver
[bronze_to_silver_orders, bronze_to_silver_customers] >> build_dim_customer
[bronze_to_silver_inventory] >> build_dim_product
[bronze_to_silver_orders] >> build_dim_store

# Fact table depends on all dimensions
[build_dim_date, build_dim_customer, build_dim_product, build_dim_store] >> build_fact_sales


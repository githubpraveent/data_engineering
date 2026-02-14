"""
Airflow DAG for running comprehensive data quality checks across all layers.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.microsoft.azure.operators.databricks import DatabricksSubmitRunOperator
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup

default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'email': ['data-engineering-team@company.com']
}

with DAG(
    'data_quality_checks',
    default_args=default_args,
    description='Comprehensive data quality checks',
    schedule_interval='0 7 * * *',  # Daily at 7 AM
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['quality', 'validation', 'testing'],
) as dag:

    # Quality checks on Bronze layer
    with TaskGroup('bronze_quality') as bronze_group:
        check_bronze_schema = DatabricksSubmitRunOperator(
            task_id='check_bronze_schema',
            databricks_conn_id='databricks_default',
            existing_cluster_id='{{ var.value.databricks_cluster_id }}',
            notebook_task={
                'notebook_path': '/Shared/quality/check_schema_bronze',
                'base_parameters': {
                    'bronze_path': 'abfss://bronze@{{ var.value.adls_storage_account }}.dfs.core.windows.net/',
                }
            },
        )

        check_bronze_completeness = DatabricksSubmitRunOperator(
            task_id='check_bronze_completeness',
            databricks_conn_id='databricks_default',
            existing_cluster_id='{{ var.value.databricks_cluster_id }}',
            notebook_task={
                'notebook_path': '/Shared/quality/check_completeness_bronze',
                'base_parameters': {
                    'bronze_path': 'abfss://bronze@{{ var.value.adls_storage_account }}.dfs.core.windows.net/',
                }
            },
        )

    # Quality checks on Silver layer
    with TaskGroup('silver_quality') as silver_group:
        check_silver_validations = DatabricksSubmitRunOperator(
            task_id='check_silver_validations',
            databricks_conn_id='databricks_default',
            existing_cluster_id='{{ var.value.databricks_cluster_id }}',
            notebook_task={
                'notebook_path': '/Shared/quality/check_validations_silver',
                'base_parameters': {
                    'silver_path': 'abfss://silver@{{ var.value.adls_storage_account }}.dfs.core.windows.net/',
                }
            },
        )

    # Quality checks on Gold layer
    with TaskGroup('gold_quality') as gold_group:
        check_gold_business_rules = DatabricksSubmitRunOperator(
            task_id='check_gold_business_rules',
            databricks_conn_id='databricks_default',
            existing_cluster_id='{{ var.value.databricks_cluster_id }}',
            notebook_task={
                'notebook_path': '/Shared/quality/check_business_rules_gold',
                'base_parameters': {
                    'gold_path': 'abfss://gold@{{ var.value.adls_storage_account }}.dfs.core.windows.net/',
                }
            },
        )

    # Generate quality report
    generate_quality_report = PythonOperator(
        task_id='generate_quality_report',
        python_callable=lambda: None,  # Placeholder - implement quality report generation
    )

    # Set dependencies
    [bronze_group, silver_group, gold_group] >> generate_quality_report


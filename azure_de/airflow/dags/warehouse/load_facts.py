"""
Airflow DAG for loading fact tables into Synapse Analytics.
Handles incremental and append loads.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.sql import SQLExecuteQueryOperator
from airflow.operators.python import PythonOperator

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
    'load_facts_synapse',
    default_args=default_args,
    description='Load fact tables to Synapse Analytics',
    schedule_interval='0 6 * * *',  # Daily at 6 AM (after dimensions)
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['warehouse', 'facts', 'synapse'],
) as dag:

    # Load Sales Fact (incremental)
    load_sales_fact = SQLExecuteQueryOperator(
        task_id='load_sales_fact',
        conn_id='synapse_sql_pool',
        sql='EXEC dwh.sp_load_sales_fact @processing_date = {{ ds }}',
    )

    # Load Order Fact (incremental)
    load_order_fact = SQLExecuteQueryOperator(
        task_id='load_order_fact',
        conn_id='synapse_sql_pool',
        sql='EXEC dwh.sp_load_order_fact @processing_date = {{ ds }}',
    )

    # Load Inventory Fact (snapshot)
    load_inventory_fact = SQLExecuteQueryOperator(
        task_id='load_inventory_fact',
        conn_id='synapse_sql_pool',
        sql='EXEC dwh.sp_load_inventory_fact @processing_date = {{ ds }}',
    )

    # Validate fact loads (referential integrity, etc.)
    validate_facts = SQLExecuteQueryOperator(
        task_id='validate_fact_loads',
        conn_id='synapse_sql_pool',
        sql='EXEC dwh.sp_validate_facts',
    )

    # Set dependencies - load facts in parallel, then validate
    [load_sales_fact, load_order_fact, load_inventory_fact] >> validate_facts


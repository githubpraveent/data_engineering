"""
Airflow DAG for orchestrating dbt transformations
Runs dbt models in the correct order with dependencies
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup
from airflow.models import Variable
import os

# Default arguments
default_args = {
    'owner': 'data_engineering',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Get environment from Airflow Variable or default to dev
ENVIRONMENT = Variable.get("DBT_ENVIRONMENT", default_var="dev")
DBT_PROJECT_DIR = Variable.get("DBT_PROJECT_DIR", default_var="/opt/airflow/dbt_project")
DBT_PROFILE = Variable.get("DBT_PROFILE", default_var="retail_data_warehouse")

def get_dbt_target():
    """Get dbt target based on environment"""
    return ENVIRONMENT

def run_dbt_command(command, select=None, full_refresh=False):
    """Build dbt command string"""
    cmd = f"cd {DBT_PROJECT_DIR} && dbt {command}"
    
    if select:
        cmd += f" --select {select}"
    
    if full_refresh:
        cmd += " --full-refresh"
    
    cmd += f" --target {get_dbt_target()}"
    cmd += f" --profiles-dir {DBT_PROJECT_DIR}"
    
    return cmd

# Create DAG
dag = DAG(
    'dbt_retail_transformations',
    default_args=default_args,
    description='Orchestrate dbt transformations for retail data warehouse',
    schedule_interval='0 2 * * *',  # Daily at 2 AM
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['dbt', 'retail', 'transformations'],
)

# Task: Check dbt connection
check_dbt_connection = BashOperator(
    task_id='check_dbt_connection',
    bash_command=run_dbt_command('debug'),
    dag=dag,
)

# Task Group: Staging Models
with TaskGroup('staging_models', dag=dag) as staging_group:
    run_staging = BashOperator(
        task_id='run_staging',
        bash_command=run_dbt_command('run', select='tag:staging'),
    )
    
    test_staging = BashOperator(
        task_id='test_staging',
        bash_command=run_dbt_command('test', select='tag:staging'),
    )
    
    run_staging >> test_staging

# Task Group: Intermediate Models
with TaskGroup('intermediate_models', dag=dag) as intermediate_group:
    run_intermediate = BashOperator(
        task_id='run_intermediate',
        bash_command=run_dbt_command('run', select='tag:intermediate'),
    )
    
    test_intermediate = BashOperator(
        task_id='test_intermediate',
        bash_command=run_dbt_command('test', select='tag:intermediate'),
    )
    
    run_intermediate >> test_intermediate

# Task Group: Dimension Models
with TaskGroup('dimension_models', dag=dag) as dimension_group:
    run_dimensions = BashOperator(
        task_id='run_dimensions',
        bash_command=run_dbt_command('run', select='tag:dimension'),
    )
    
    test_dimensions = BashOperator(
        task_id='test_dimensions',
        bash_command=run_dbt_command('test', select='tag:dimension'),
    )
    
    run_dimensions >> test_dimensions

# Task Group: Fact Models
with TaskGroup('fact_models', dag=dag) as fact_group:
    run_facts = BashOperator(
        task_id='run_facts',
        bash_command=run_dbt_command('run', select='tag:fact'),
    )
    
    test_facts = BashOperator(
        task_id='test_facts',
        bash_command=run_dbt_command('test', select='tag:fact'),
    )
    
    run_facts >> test_facts

# Task Group: Mart Models
with TaskGroup('mart_models', dag=dag) as mart_group:
    run_marts = BashOperator(
        task_id='run_marts',
        bash_command=run_dbt_command('run', select='tag:mart'),
    )
    
    test_marts = BashOperator(
        task_id='test_marts',
        bash_command=run_dbt_command('test', select='tag:mart'),
    )
    
    run_marts >> test_marts

# Task: Run all tests (final validation)
run_all_tests = BashOperator(
    task_id='run_all_tests',
    bash_command=run_dbt_command('test'),
    dag=dag,
)

# Task: Generate documentation
generate_docs = BashOperator(
    task_id='generate_dbt_docs',
    bash_command=run_dbt_command('docs generate'),
    dag=dag,
)

# Task: Data quality check (custom)
def data_quality_check(**context):
    """Custom data quality validation"""
    import subprocess
    result = subprocess.run(
        run_dbt_command('test', select='test_type:data'),
        shell=True,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise Exception(f"Data quality tests failed: {result.stderr}")
    return "Data quality checks passed"

quality_check = PythonOperator(
    task_id='data_quality_check',
    python_callable=data_quality_check,
    dag=dag,
)

# Define task dependencies
check_dbt_connection >> staging_group
staging_group >> intermediate_group
intermediate_group >> dimension_group
dimension_group >> fact_group
fact_group >> mart_group
mart_group >> run_all_tests
run_all_tests >> quality_check
quality_check >> generate_docs


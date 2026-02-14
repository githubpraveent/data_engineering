from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

from common import DEFAULT_ARGS, DAG_START_DATE
from ingestion.batch.run import run_batch_pipeline
from scripts.load_sample_data import main as load_sample_data
from quality.checks import run_quality_checks

with DAG(
    dag_id="batch_claims_etl",
    default_args=DEFAULT_ARGS,
    schedule_interval="0 2 * * *",
    start_date=DAG_START_DATE,
    catchup=False,
    tags=["batch", "claims"],
) as dag:
    extract_and_load = PythonOperator(
        task_id="extract_and_load",
        python_callable=run_batch_pipeline,
    )

    load_sample = PythonOperator(
        task_id="load_sample_data",
        python_callable=load_sample_data,
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/airflow/dags/../../dbt && dbt run --profiles-dir .",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="cd /opt/airflow/dags/../../dbt && dbt test --profiles-dir .",
    )

    quality_checks = PythonOperator(
        task_id="quality_checks",
        python_callable=run_quality_checks,
    )

    publish_databricks = BashOperator(
        task_id="publish_databricks",
        bash_command="python /opt/airflow/dags/../../ingestion/batch/publish_databricks.py",
    )

    load_sample >> extract_and_load >> dbt_run >> dbt_test >> quality_checks >> publish_databricks

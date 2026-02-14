from airflow import DAG
from airflow.operators.python import PythonOperator

from common import DEFAULT_ARGS, DAG_START_DATE
from ingestion.streaming.consumer import run_streaming_consumer

with DAG(
    dag_id="streaming_claims_ingest",
    default_args=DEFAULT_ARGS,
    schedule_interval="*/5 * * * *",
    start_date=DAG_START_DATE,
    catchup=False,
    tags=["streaming", "claims"],
) as dag:
    consume_events = PythonOperator(
        task_id="consume_events",
        python_callable=run_streaming_consumer,
    )

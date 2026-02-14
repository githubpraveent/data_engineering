import os
import sys

from datetime import datetime, timedelta

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), \"..\", \"..\"))
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

DEFAULT_ARGS = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

ENV = os.getenv("ENV", "local")

SNOWFLAKE_CONN_ID = os.getenv("SNOWFLAKE_CONN_ID", "snowflake_default")
SQLSERVER_CONN_ID = os.getenv("SQLSERVER_CONN_ID", "sqlserver_default")
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")

DAG_START_DATE = datetime(2024, 1, 1)

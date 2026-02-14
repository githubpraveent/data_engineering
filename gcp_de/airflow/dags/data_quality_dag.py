"""
Data Quality DAG
Runs comprehensive data quality checks on staging and curated data.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryCheckOperator,
    BigQueryValueCheckOperator,
    BigQueryIntervalCheckOperator
)
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import os

default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'start_date': days_ago(1),
}

PROJECT_ID = os.environ.get('GCP_PROJECT', 'your-project-id')
STAGING_DATASET = os.environ.get('STAGING_DATASET', 'staging_dev')
CURATED_DATASET = os.environ.get('CURATED_DATASET', 'curated_dev')

with DAG(
    'data_quality_checks',
    default_args=default_args,
    description='Comprehensive data quality validation',
    schedule_interval='0 3 * * *',  # Daily at 3 AM UTC
    catchup=False,
    max_active_runs=1,
    tags=['data-quality', 'validation', 'bigquery'],
) as dag:

    # Check 1: No null primary keys in staging
    check_null_primary_keys = BigQueryCheckOperator(
        task_id='check_null_primary_keys',
        sql=f"""
        SELECT COUNT(*) as null_count
        FROM `{PROJECT_ID}.{STAGING_DATASET}.transactions_staging`
        WHERE transaction_id IS NULL
        OR customer_id IS NULL
        OR product_id IS NULL
        HAVING null_count = 0
        """,
        use_legacy_sql=False,
    )

    # Check 2: Data freshness (data should be loaded within last 24 hours)
    check_data_freshness = BigQueryValueCheckOperator(
        task_id='check_data_freshness',
        sql=f"""
        SELECT MAX(load_timestamp) as latest_load
        FROM `{PROJECT_ID}.{CURATED_DATASET}.sales_fact`
        """,
        pass_value=datetime.now() - timedelta(hours=25),
        tolerance=0.1,
        use_legacy_sql=False,
    )

    # Check 3: Referential integrity - all foreign keys exist in dimensions
    check_referential_integrity = BigQueryCheckOperator(
        task_id='check_referential_integrity',
        sql=f"""
        SELECT COUNT(*) as orphaned_records
        FROM `{PROJECT_ID}.{CURATED_DATASET}.sales_fact` sf
        LEFT JOIN `{PROJECT_ID}.{CURATED_DATASET}.customer_dimension` cd
        ON sf.customer_id = cd.customer_id AND cd.is_current = TRUE
        LEFT JOIN `{PROJECT_ID}.{CURATED_DATASET}.product_dimension` pd
        ON sf.product_id = pd.product_id AND pd.is_current = TRUE
        LEFT JOIN `{PROJECT_ID}.{CURATED_DATASET}.store_dimension` sd
        ON sf.store_id = sd.store_id
        WHERE cd.customer_id IS NULL
        OR pd.product_id IS NULL
        OR sd.store_id IS NULL
        HAVING orphaned_records = 0
        """,
        use_legacy_sql=False,
    )

    # Check 4: Data completeness - expected row count range
    check_row_count = BigQueryIntervalCheckOperator(
        task_id='check_row_count',
        table=f'{PROJECT_ID}.{CURATED_DATASET}.sales_fact',
        metrics_thresholds={
            'COUNT(*)': {
                'min_value': 1000,  # Minimum expected rows
                'max_value': 10000000,  # Maximum expected rows
            }
        },
        date_filter_column='transaction_timestamp',
        days_back=1,
        use_legacy_sql=False,
    )

    # Check 5: Data validity - no negative amounts
    check_negative_amounts = BigQueryCheckOperator(
        task_id='check_negative_amounts',
        sql=f"""
        SELECT COUNT(*) as negative_count
        FROM `{PROJECT_ID}.{CURATED_DATASET}.sales_fact`
        WHERE total_amount < 0
        OR quantity < 0
        OR unit_price < 0
        HAVING negative_count = 0
        """,
        use_legacy_sql=False,
    )

    # Check 6: Uniqueness - no duplicate transaction IDs
    check_duplicate_transactions = BigQueryCheckOperator(
        task_id='check_duplicate_transactions',
        sql=f"""
        SELECT COUNT(*) as duplicate_count
        FROM (
            SELECT transaction_id, COUNT(*) as cnt
            FROM `{PROJECT_ID}.{CURATED_DATASET}.sales_fact`
            GROUP BY transaction_id
            HAVING cnt > 1
        )
        HAVING duplicate_count = 0
        """,
        use_legacy_sql=False,
    )

    # Check 7: SCD Type 2 integrity - only one current record per key
    check_scd2_integrity = BigQueryCheckOperator(
        task_id='check_scd2_integrity',
        sql=f"""
        SELECT COUNT(*) as invalid_scd2
        FROM (
            SELECT customer_id, COUNT(*) as current_count
            FROM `{PROJECT_ID}.{CURATED_DATASET}.customer_dimension`
            WHERE is_current = TRUE
            GROUP BY customer_id
            HAVING current_count > 1
        )
        HAVING invalid_scd2 = 0
        """,
        use_legacy_sql=False,
    )

    # Check 8: Data consistency - sum of line items equals transaction total
    check_transaction_totals = BigQueryCheckOperator(
        task_id='check_transaction_totals',
        sql=f"""
        SELECT COUNT(*) as inconsistent_transactions
        FROM (
            SELECT 
                transaction_id,
                SUM(quantity * unit_price) as calculated_total,
                SUM(total_amount) as stored_total
            FROM `{PROJECT_ID}.{CURATED_DATASET}.sales_fact`
            GROUP BY transaction_id
            HAVING ABS(calculated_total - stored_total) > 0.01
        )
        HAVING inconsistent_transactions = 0
        """,
        use_legacy_sql=False,
    )

    # All checks run in parallel
    [
        check_null_primary_keys,
        check_data_freshness,
        check_referential_integrity,
        check_row_count,
        check_negative_amounts,
        check_duplicate_transactions,
        check_scd2_integrity,
        check_transaction_totals,
    ]


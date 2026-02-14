"""
Airflow DAG for Data Quality Monitoring
Runs comprehensive data quality checks across all layers
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup
from airflow.models import Variable

# Default arguments
default_args = {
    'owner': 'data_engineering',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'snowflake_conn_id': 'snowflake_default',
}

# Environment configuration
ENV = Variable.get("ENVIRONMENT", default_var="DEV")
RAW_DATABASE = f"{ENV}_RAW"
STAGING_DATABASE = f"{ENV}_STAGING"
DW_DATABASE = f"{ENV}_DW"

# DAG definition
dag = DAG(
    'retail_data_quality_monitoring',
    default_args=default_args,
    description='Comprehensive data quality checks for retail data pipeline',
    schedule_interval=timedelta(hours=6),  # Run every 6 hours
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['data-quality', 'monitoring', 'retail'],
)


def check_data_freshness(**context):
    """Check if data is being loaded within expected timeframes"""
    hook = SnowflakeHook(snowflake_conn_id='snowflake_default')
    
    checks = {
        'raw_pos': {
            'max_age_hours': 2,
            'query': f"SELECT MAX(load_timestamp) FROM {RAW_DATABASE}.BRONZE.raw_pos"
        },
        'stg_pos': {
            'max_age_hours': 3,
            'query': f"SELECT MAX(created_at) FROM {STAGING_DATABASE}.SILVER.stg_pos"
        },
        'fact_sales': {
            'max_age_hours': 4,
            'query': f"SELECT MAX(created_at) FROM {DW_DATABASE}.FACTS.fact_sales"
        }
    }
    
    results = {}
    for table, config in checks.items():
        result = hook.get_first(config['query'])
        if result and result[0]:
            latest_timestamp = result[0]
            age_hours = (datetime.now() - latest_timestamp).total_seconds() / 3600
            
            results[table] = {
                'latest_timestamp': latest_timestamp,
                'age_hours': age_hours,
                'is_fresh': age_hours <= config['max_age_hours']
            }
            
            if not results[table]['is_fresh']:
                raise ValueError(
                    f"Data freshness check failed for {table}: "
                    f"Data is {age_hours:.2f} hours old (max: {config['max_age_hours']} hours)"
                )
        else:
            results[table] = {
                'latest_timestamp': None,
                'age_hours': None,
                'is_fresh': False
            }
            raise ValueError(f"No data found in {table}")
    
    return results


# Task Group: Completeness Checks
with TaskGroup('completeness_checks', dag=dag) as completeness_group:
    # Check for missing critical fields
    check_null_fields = SnowflakeOperator(
        task_id='check_null_fields',
        sql=f"""
        SELECT 
            'raw_pos' as table_name,
            COUNT(*) as total_rows,
            SUM(CASE WHEN transaction_id IS NULL THEN 1 ELSE 0 END) as null_transaction_id,
            SUM(CASE WHEN store_id IS NULL THEN 1 ELSE 0 END) as null_store_id,
            SUM(CASE WHEN product_id IS NULL THEN 1 ELSE 0 END) as null_product_id
        FROM {RAW_DATABASE}.BRONZE.raw_pos
        WHERE load_timestamp >= CURRENT_TIMESTAMP() - INTERVAL '24 hours'
        HAVING null_transaction_id > 0 OR null_store_id > 0 OR null_product_id > 0
        """,
        dag=dag,
    )


# Task Group: Accuracy Checks
with TaskGroup('accuracy_checks', dag=dag) as accuracy_group:
    # Check for negative amounts
    check_negative_amounts = SnowflakeOperator(
        task_id='check_negative_amounts',
        sql=f"""
        SELECT 
            'stg_pos' as table_name,
            COUNT(*) as invalid_rows
        FROM {STAGING_DATABASE}.SILVER.stg_pos
        WHERE total_amount < 0 
           OR unit_price < 0 
           OR quantity <= 0
           OR created_at >= CURRENT_TIMESTAMP() - INTERVAL '24 hours'
        HAVING COUNT(*) > 0
        """,
        dag=dag,
    )
    
    # Check for unrealistic values
    check_unrealistic_values = SnowflakeOperator(
        task_id='check_unrealistic_values',
        sql=f"""
        SELECT 
            'stg_pos' as table_name,
            COUNT(*) as invalid_rows
        FROM {STAGING_DATABASE}.SILVER.stg_pos
        WHERE unit_price > 100000
           OR quantity > 10000
           OR total_amount > 1000000
           OR created_at >= CURRENT_TIMESTAMP() - INTERVAL '24 hours'
        HAVING COUNT(*) > 0
        """,
        dag=dag,
    )


# Task Group: Consistency Checks
with TaskGroup('consistency_checks', dag=dag) as consistency_group:
    # Check referential integrity
    check_referential_integrity = SnowflakeOperator(
        task_id='check_referential_integrity',
        sql=f"""
        SELECT 
            'fact_sales' as fact_table,
            COUNT(*) as orphaned_records
        FROM {DW_DATABASE}.FACTS.fact_sales fs
        LEFT JOIN {DW_DATABASE}.DIMENSIONS.dim_product dp ON fs.product_key = dp.product_key
        LEFT JOIN {DW_DATABASE}.DIMENSIONS.dim_store ds ON fs.store_key = ds.store_key
        LEFT JOIN {DW_DATABASE}.DIMENSIONS.dim_date dd ON fs.date_key = dd.date_key
        WHERE dp.product_key IS NULL 
           OR ds.store_key IS NULL 
           OR dd.date_key IS NULL
        HAVING COUNT(*) > 0
        """,
        dag=dag,
    )
    
    # Check for duplicate transactions
    check_duplicates = SnowflakeOperator(
        task_id='check_duplicates',
        sql=f"""
        SELECT 
            transaction_id,
            product_key,
            COUNT(*) as duplicate_count
        FROM {DW_DATABASE}.FACTS.fact_sales
        GROUP BY transaction_id, product_key
        HAVING COUNT(*) > 1
        """,
        dag=dag,
    )


# Task Group: Timeliness Checks
with TaskGroup('timeliness_checks', dag=dag) as timeliness_group:
    # Check data freshness
    check_freshness = PythonOperator(
        task_id='check_data_freshness',
        python_callable=check_data_freshness,
        dag=dag,
    )


# Task Group: Business Rule Checks
with TaskGroup('business_rule_checks', dag=dag) as business_rules_group:
    # Check business rules
    check_business_rules = SnowflakeOperator(
        task_id='check_business_rules',
        sql=f"""
        -- Example: Check that total_amount = (quantity * unit_price) - discount_amount + tax_amount
        SELECT 
            'stg_pos' as table_name,
            COUNT(*) as rule_violations
        FROM {STAGING_DATABASE}.SILVER.stg_pos
        WHERE ABS(total_amount - ((quantity * unit_price) - discount_amount + tax_amount)) > 0.01
          AND created_at >= CURRENT_TIMESTAMP() - INTERVAL '24 hours'
        HAVING COUNT(*) > 0
        """,
        dag=dag,
    )


# Task: Generate quality report
generate_quality_report = SnowflakeOperator(
    task_id='generate_quality_report',
    sql=f"""
    CREATE OR REPLACE TABLE {DW_DATABASE}.MONITORING.data_quality_report AS
    SELECT 
        CURRENT_TIMESTAMP() as report_timestamp,
        'raw_pos' as table_name,
        COUNT(*) as total_rows,
        SUM(CASE WHEN transaction_id IS NULL THEN 1 ELSE 0 END) as null_transaction_id,
        SUM(CASE WHEN store_id IS NULL THEN 1 ELSE 0 END) as null_store_id
    FROM {RAW_DATABASE}.BRONZE.raw_pos
    WHERE load_timestamp >= CURRENT_TIMESTAMP() - INTERVAL '24 hours'
    
    UNION ALL
    
    SELECT 
        CURRENT_TIMESTAMP() as report_timestamp,
        'stg_pos' as table_name,
        COUNT(*) as total_rows,
        SUM(CASE WHEN is_valid = FALSE THEN 1 ELSE 0 END) as invalid_rows,
        0 as null_store_id
    FROM {STAGING_DATABASE}.SILVER.stg_pos
    WHERE created_at >= CURRENT_TIMESTAMP() - INTERVAL '24 hours'
    """,
    dag=dag,
)

# Task dependencies
[completeness_group, accuracy_group, consistency_group, timeliness_group, business_rules_group] >> generate_quality_report


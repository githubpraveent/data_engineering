"""
SCD Dimension DAG
Handles Slowly Changing Dimensions (Type 1 and Type 2) for dimension tables.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryCheckOperator
from airflow.utils.dates import days_ago
import os

default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': days_ago(1),
}

PROJECT_ID = os.environ.get('GCP_PROJECT', 'your-project-id')
STAGING_DATASET = os.environ.get('STAGING_DATASET', 'staging_dev')
CURATED_DATASET = os.environ.get('CURATED_DATASET', 'curated_dev')

with DAG(
    'scd_dimension_updates',
    default_args=default_args,
    description='Update dimension tables with SCD Type 1 and Type 2 logic',
    schedule_interval='0 * * * *',  # Hourly
    catchup=False,
    max_active_runs=1,
    tags=['scd', 'dimensions', 'bigquery'],
) as dag:

    # SCD Type 2: Customer Dimension
    update_customer_dimension_scd2 = BigQueryInsertJobOperator(
        task_id='update_customer_dimension_scd2',
        configuration={
            'query': {
                'query': f"""
                -- SCD Type 2: Customer Dimension
                -- Expire old records
                UPDATE `{PROJECT_ID}.{CURATED_DATASET}.customer_dimension`
                SET 
                    is_current = FALSE,
                    expiration_date = CURRENT_TIMESTAMP()
                WHERE is_current = TRUE
                AND customer_id IN (
                    SELECT DISTINCT customer_id
                    FROM `{PROJECT_ID}.{STAGING_DATASET}.customers_staging`
                    WHERE load_date = DATE('{{{{ ds }}}}')
                )
                AND customer_id NOT IN (
                    -- Keep current if no changes
                    SELECT customer_id
                    FROM `{PROJECT_ID}.{STAGING_DATASET}.customers_staging` cs
                    INNER JOIN `{PROJECT_ID}.{CURATED_DATASET}.customer_dimension` cd
                    ON cs.customer_id = cd.customer_id
                    WHERE cd.is_current = TRUE
                    AND cs.load_date = DATE('{{{{ ds }}}}')
                    AND cs.first_name = cd.first_name
                    AND cs.last_name = cd.last_name
                    AND cs.email = cd.email
                    AND cs.address = cd.address
                    AND cs.phone = cd.phone
                );

                -- Insert new records for changed customers
                INSERT INTO `{PROJECT_ID}.{CURATED_DATASET}.customer_dimension`
                (
                    customer_id,
                    first_name,
                    last_name,
                    email,
                    address,
                    phone,
                    customer_segment,
                    registration_date,
                    effective_date,
                    expiration_date,
                    is_current,
                    load_timestamp
                )
                SELECT 
                    cs.customer_id,
                    cs.first_name,
                    cs.last_name,
                    cs.email,
                    cs.address,
                    cs.phone,
                    cs.customer_segment,
                    cs.registration_date,
                    CURRENT_TIMESTAMP() as effective_date,
                    CAST(NULL AS TIMESTAMP) as expiration_date,
                    TRUE as is_current,
                    CURRENT_TIMESTAMP() as load_timestamp
                FROM `{PROJECT_ID}.{STAGING_DATASET}.customers_staging` cs
                LEFT JOIN `{PROJECT_ID}.{CURATED_DATASET}.customer_dimension` cd
                ON cs.customer_id = cd.customer_id
                AND cd.is_current = TRUE
                WHERE cs.load_date = DATE('{{{{ ds }}}}')
                AND (
                    cd.customer_id IS NULL  -- New customer
                    OR (
                        -- Changed customer (SCD Type 2)
                        (cs.first_name != cd.first_name OR cs.first_name IS NULL AND cd.first_name IS NOT NULL)
                        OR (cs.last_name != cd.last_name OR cs.last_name IS NULL AND cd.last_name IS NOT NULL)
                        OR (cs.email != cd.email OR cs.email IS NULL AND cd.email IS NOT NULL)
                        OR (cs.address != cd.address OR cs.address IS NULL AND cd.address IS NOT NULL)
                        OR (cs.phone != cd.phone OR cs.phone IS NULL AND cd.phone IS NOT NULL)
                        OR (cs.customer_segment != cd.customer_segment OR cs.customer_segment IS NULL AND cd.customer_segment IS NOT NULL)
                    )
                );
                """,
                'useLegacySql': False,
            }
        },
        project_id=PROJECT_ID,
    )

    # SCD Type 2: Product Dimension
    update_product_dimension_scd2 = BigQueryInsertJobOperator(
        task_id='update_product_dimension_scd2',
        configuration={
            'query': {
                'query': f"""
                -- SCD Type 2: Product Dimension
                UPDATE `{PROJECT_ID}.{CURATED_DATASET}.product_dimension`
                SET 
                    is_current = FALSE,
                    expiration_date = CURRENT_TIMESTAMP()
                WHERE is_current = TRUE
                AND product_id IN (
                    SELECT DISTINCT product_id
                    FROM `{PROJECT_ID}.{STAGING_DATASET}.products_staging`
                    WHERE load_date = DATE('{{{{ ds }}}}')
                )
                AND product_id NOT IN (
                    SELECT product_id
                    FROM `{PROJECT_ID}.{STAGING_DATASET}.products_staging` ps
                    INNER JOIN `{PROJECT_ID}.{CURATED_DATASET}.product_dimension` pd
                    ON ps.product_id = pd.product_id
                    WHERE pd.is_current = TRUE
                    AND ps.load_date = DATE('{{{{ ds }}}}')
                    AND ps.product_name = pd.product_name
                    AND ps.category = pd.category
                    AND ps.price = pd.price
                    AND ps.description = pd.description
                );

                INSERT INTO `{PROJECT_ID}.{CURATED_DATASET}.product_dimension`
                (
                    product_id,
                    product_name,
                    category,
                    subcategory,
                    price,
                    cost,
                    description,
                    brand,
                    effective_date,
                    expiration_date,
                    is_current,
                    load_timestamp
                )
                SELECT 
                    ps.product_id,
                    ps.product_name,
                    ps.category,
                    ps.subcategory,
                    ps.price,
                    ps.cost,
                    ps.description,
                    ps.brand,
                    CURRENT_TIMESTAMP() as effective_date,
                    CAST(NULL AS TIMESTAMP) as expiration_date,
                    TRUE as is_current,
                    CURRENT_TIMESTAMP() as load_timestamp
                FROM `{PROJECT_ID}.{STAGING_DATASET}.products_staging` ps
                LEFT JOIN `{PROJECT_ID}.{CURATED_DATASET}.product_dimension` pd
                ON ps.product_id = pd.product_id
                AND pd.is_current = TRUE
                WHERE ps.load_date = DATE('{{{{ ds }}}}')
                AND (
                    pd.product_id IS NULL
                    OR (
                        (ps.product_name != pd.product_name OR ps.product_name IS NULL AND pd.product_name IS NOT NULL)
                        OR (ps.category != pd.category OR ps.category IS NULL AND pd.category IS NOT NULL)
                        OR (ps.price != pd.price OR ps.price IS NULL AND pd.price IS NOT NULL)
                        OR (ps.description != pd.description OR ps.description IS NULL AND pd.description IS NOT NULL)
                    )
                );
                """,
                'useLegacySql': False,
            }
        },
        project_id=PROJECT_ID,
    )

    # SCD Type 1: Store Dimension (overwrite current values)
    update_store_dimension_scd1 = BigQueryInsertJobOperator(
        task_id='update_store_dimension_scd1',
        configuration={
            'query': {
                'query': f"""
                -- SCD Type 1: Store Dimension (overwrite)
                MERGE `{PROJECT_ID}.{CURATED_DATASET}.store_dimension` AS target
                USING (
                    SELECT 
                        store_id,
                        store_name,
                        address,
                        city,
                        state,
                        zip_code,
                        country,
                        store_manager,
                        phone,
                        opening_date,
                        store_type,
                        square_feet,
                        CURRENT_TIMESTAMP() as load_timestamp
                    FROM `{PROJECT_ID}.{STAGING_DATASET}.stores_staging`
                    WHERE load_date = DATE('{{{{ ds }}}}')
                ) AS source
                ON target.store_id = source.store_id
                WHEN MATCHED THEN
                    UPDATE SET
                        store_name = source.store_name,
                        address = source.address,
                        city = source.city,
                        state = source.state,
                        zip_code = source.zip_code,
                        country = source.country,
                        store_manager = source.store_manager,
                        phone = source.phone,
                        store_type = source.store_type,
                        square_feet = source.square_feet,
                        load_timestamp = source.load_timestamp
                WHEN NOT MATCHED THEN
                    INSERT (
                        store_id,
                        store_name,
                        address,
                        city,
                        state,
                        zip_code,
                        country,
                        store_manager,
                        phone,
                        opening_date,
                        store_type,
                        square_feet,
                        load_timestamp
                    )
                    VALUES (
                        source.store_id,
                        source.store_name,
                        source.address,
                        source.city,
                        source.state,
                        source.zip_code,
                        source.country,
                        source.store_manager,
                        source.phone,
                        source.opening_date,
                        source.store_type,
                        source.square_feet,
                        source.load_timestamp
                    );
                """,
                'useLegacySql': False,
            }
        },
        project_id=PROJECT_ID,
    )

    # Validation: Check SCD Type 2 integrity
    validate_scd2_integrity = BigQueryCheckOperator(
        task_id='validate_scd2_integrity',
        sql=f"""
        SELECT COUNT(*) as invalid_records
        FROM (
            SELECT customer_id, COUNT(*) as current_count
            FROM `{PROJECT_ID}.{CURATED_DATASET}.customer_dimension`
            WHERE is_current = TRUE
            GROUP BY customer_id
            HAVING current_count > 1
        )
        """,
        use_legacy_sql=False,
    )

    # Define dependencies
    update_customer_dimension_scd2 >> validate_scd2_integrity
    update_product_dimension_scd2 >> validate_scd2_integrity
    update_store_dimension_scd1


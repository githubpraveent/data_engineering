"""
Dagster Definitions
Main entry point for Dagster code location
"""

from dagster import Definitions, load_assets_from_modules, ScheduleDefinition, DefaultSensorStatus
from dagster_snowflake import SnowflakeResource
import os

# Import assets and jobs
from dagster_code.assets import (
    raw_pos_data,
    raw_orders_data,
    raw_inventory_data,
    stg_pos_data,
    stg_orders_data,
    stg_inventory_data,
    dim_customer,
    dim_product,
    fact_sales,
)

from dagster_code.jobs.ingestion_job import ingestion_job
from dagster_code.jobs.transformation_job import transformation_job
from dagster_code.jobs.data_quality_job import data_quality_job

# Environment configuration
ENV = os.getenv("ENVIRONMENT", "DEV")

# Load all assets
import dagster_code.assets as assets_module
all_assets = load_assets_from_modules([assets_module])

# Snowflake resource configuration
snowflake_resource = SnowflakeResource(
    account=os.getenv("SNOWFLAKE_ACCOUNT", "your_account"),
    user=os.getenv("SNOWFLAKE_USER", "your_user"),
    password=os.getenv("SNOWFLAKE_PASSWORD", "your_password"),
    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "WH_TRANS"),
    database=os.getenv("SNOWFLAKE_DATABASE", f"{ENV}_RAW"),
    schema=os.getenv("SNOWFLAKE_SCHEMA", "BRONZE"),
)

# Schedules
ingestion_schedule = ScheduleDefinition(
    job=ingestion_job,
    cron_schedule="0 * * * *",  # Every hour
    name="ingestion_schedule",
    description="Schedule for data ingestion pipeline",
)

transformation_schedule = ScheduleDefinition(
    job=transformation_job,
    cron_schedule="0 * * * *",  # Every hour
    name="transformation_schedule",
    description="Schedule for data transformation pipeline",
)

data_quality_schedule = ScheduleDefinition(
    job=data_quality_job,
    cron_schedule="0 */6 * * *",  # Every 6 hours
    name="data_quality_schedule",
    description="Schedule for data quality monitoring",
)

# Definitions
defs = Definitions(
    assets=all_assets,
    jobs=[ingestion_job, transformation_job, data_quality_job],
    schedules=[ingestion_schedule, transformation_schedule, data_quality_schedule],
    resources={
        "snowflake": snowflake_resource,
    },
)


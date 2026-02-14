"""
Dagster Job for Data Ingestion
Orchestrates the ingestion of data from source systems into Snowflake
"""

from dagster import job, op, OpExecutionContext
from dagster_snowflake import SnowflakeResource
from typing import Dict, Any
import os

ENV = os.getenv("ENVIRONMENT", "DEV")
RAW_DATABASE = f"{ENV}_RAW"
RAW_SCHEMA = "BRONZE"


@op(
    description="Check Snowpipe status and file ingestion"
)
def check_snowpipe_status(context: OpExecutionContext, snowflake: SnowflakeResource) -> Dict[str, Any]:
    """Check the status of Snowpipe pipes"""
    with snowflake.get_connection() as conn:
        cursor = conn.cursor()
        
        pipes = ['pipe_pos_data', 'pipe_orders_data', 'pipe_inventory_data']
        results = {}
        
        for pipe in pipes:
            query = f"""
            SELECT SYSTEM$PIPE_STATUS('{RAW_DATABASE}.{RAW_SCHEMA}.{pipe}') as status
            """
            cursor.execute(query)
            result = cursor.fetchone()
            results[pipe] = result[0] if result else None
            context.log.info(f"Pipe {pipe} status: {results[pipe]}")
        
        return {"pipe_status": results, "status": "success"}


@op(
    description="Validate that data was ingested successfully"
)
def validate_ingestion(context: OpExecutionContext, snowflake: SnowflakeResource, pipe_status: Dict[str, Any]) -> Dict[str, Any]:
    """Validate ingestion by checking row counts"""
    with snowflake.get_connection() as conn:
        cursor = conn.cursor()
        
        tables = ['raw_pos', 'raw_orders', 'raw_inventory']
        validation_results = {}
        
        for table in tables:
            query = f"""
            SELECT 
                COUNT(*) as row_count,
                MAX(load_timestamp) as latest_load
            FROM {RAW_DATABASE}.{RAW_SCHEMA}.{table}
            WHERE load_timestamp >= CURRENT_TIMESTAMP() - INTERVAL '2 hours'
            """
            cursor.execute(query)
            result = cursor.fetchone()
            
            row_count = result[0] if result else 0
            latest_load = result[1] if result else None
            
            validation_results[table] = {
                'row_count': row_count,
                'latest_load': str(latest_load) if latest_load else None
            }
            
            context.log.info(
                f"Table {table}: {row_count} rows, Latest load: {latest_load}"
            )
        
        # Fail if no data ingested
        total_rows = sum(r['row_count'] for r in validation_results.values())
        if total_rows == 0:
            raise ValueError("No data ingested in the last 2 hours")
        
        return {
            "validation_results": validation_results,
            "total_rows": total_rows,
            "status": "success"
        }


@op(
    description="Run data quality checks on ingested data"
)
def data_quality_checks(context: OpExecutionContext, snowflake: SnowflakeResource, validation: Dict[str, Any]) -> Dict[str, Any]:
    """Run data quality checks on raw data"""
    with snowflake.get_connection() as conn:
        cursor = conn.cursor()
        
        query = f"""
        SELECT 
            'raw_pos' as table_name,
            COUNT(*) as total_rows,
            SUM(CASE WHEN transaction_id IS NULL THEN 1 ELSE 0 END) as null_transaction_id,
            SUM(CASE WHEN store_id IS NULL THEN 1 ELSE 0 END) as null_store_id,
            SUM(CASE WHEN product_id IS NULL THEN 1 ELSE 0 END) as null_product_id
        FROM {RAW_DATABASE}.{RAW_SCHEMA}.raw_pos
        WHERE load_timestamp >= CURRENT_TIMESTAMP() - INTERVAL '2 hours'
        """
        cursor.execute(query)
        result = cursor.fetchone()
        
        quality_results = {
            "table_name": result[0] if result else None,
            "total_rows": result[1] if result else 0,
            "null_transaction_id": result[2] if result else 0,
            "null_store_id": result[3] if result else 0,
            "null_product_id": result[4] if result else 0,
        }
        
        context.log.info(f"Quality check results: {quality_results}")
        
        # Fail if critical fields are null
        if quality_results["null_transaction_id"] > 0 or quality_results["null_store_id"] > 0:
            raise ValueError(f"Data quality check failed: {quality_results}")
        
        return {
            "quality_results": quality_results,
            "status": "success"
        }


@job(
    description="Ingest retail data from source systems into Snowflake",
    tags={"orchestrator": "dagster", "layer": "ingestion"}
)
def ingestion_job():
    """Job definition for data ingestion pipeline"""
    pipe_status = check_snowpipe_status()
    validation = validate_ingestion(pipe_status)
    data_quality_checks(validation)


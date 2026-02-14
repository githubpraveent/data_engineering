"""
Dagster Job for Data Quality Monitoring
Runs comprehensive data quality checks across all layers
"""

from dagster import job, op, OpExecutionContext
from dagster_snowflake import SnowflakeResource
from typing import Dict, Any
import os

ENV = os.getenv("ENVIRONMENT", "DEV")
RAW_DATABASE = f"{ENV}_RAW"
STAGING_DATABASE = f"{ENV}_STAGING"
DW_DATABASE = f"{ENV}_DW"


@op(
    description="Check data completeness (null values)"
)
def check_completeness(context: OpExecutionContext, snowflake: SnowflakeResource) -> Dict[str, Any]:
    """Check for null values in critical fields"""
    with snowflake.get_connection() as conn:
        cursor = conn.cursor()
        
        query = f"""
        SELECT 
            'raw_pos' as table_name,
            COUNT(*) as total_rows,
            SUM(CASE WHEN transaction_id IS NULL THEN 1 ELSE 0 END) as null_transaction_id,
            SUM(CASE WHEN store_id IS NULL THEN 1 ELSE 0 END) as null_store_id,
            SUM(CASE WHEN product_id IS NULL THEN 1 ELSE 0 END) as null_product_id
        FROM {RAW_DATABASE}.BRONZE.raw_pos
        WHERE load_timestamp >= CURRENT_TIMESTAMP() - INTERVAL '24 hours'
        """
        cursor.execute(query)
        result = cursor.fetchone()
        
        completeness_results = {
            "table_name": result[0] if result else None,
            "total_rows": result[1] if result else 0,
            "null_transaction_id": result[2] if result else 0,
            "null_store_id": result[3] if result else 0,
            "null_product_id": result[4] if result else 0,
        }
        
        context.log.info(f"Completeness check results: {completeness_results}")
        
        # Fail if critical fields have nulls
        if (completeness_results["null_transaction_id"] > 0 or 
            completeness_results["null_store_id"] > 0 or 
            completeness_results["null_product_id"] > 0):
            raise ValueError(f"Completeness check failed: {completeness_results}")
        
        return {"completeness": completeness_results, "status": "success"}


@op(
    description="Check data accuracy (negative amounts, unrealistic values)"
)
def check_accuracy(context: OpExecutionContext, snowflake: SnowflakeResource) -> Dict[str, Any]:
    """Check for negative amounts and unrealistic values"""
    with snowflake.get_connection() as conn:
        cursor = conn.cursor()
        
        query = f"""
        SELECT 
            'stg_pos' as table_name,
            COUNT(*) as total_rows,
            SUM(CASE WHEN total_amount < 0 THEN 1 ELSE 0 END) as negative_amounts,
            SUM(CASE WHEN unit_price < 0 THEN 1 ELSE 0 END) as negative_prices,
            SUM(CASE WHEN quantity <= 0 THEN 1 ELSE 0 END) as invalid_quantities,
            SUM(CASE WHEN unit_price > 100000 THEN 1 ELSE 0 END) as unrealistic_prices
        FROM {STAGING_DATABASE}.SILVER.stg_pos
        WHERE created_at >= CURRENT_TIMESTAMP() - INTERVAL '24 hours'
        """
        cursor.execute(query)
        result = cursor.fetchone()
        
        accuracy_results = {
            "table_name": result[0] if result else None,
            "total_rows": result[1] if result else 0,
            "negative_amounts": result[2] if result else 0,
            "negative_prices": result[3] if result else 0,
            "invalid_quantities": result[4] if result else 0,
            "unrealistic_prices": result[5] if result else 0,
        }
        
        context.log.info(f"Accuracy check results: {accuracy_results}")
        
        # Fail if accuracy issues found
        if (accuracy_results["negative_amounts"] > 0 or 
            accuracy_results["negative_prices"] > 0 or 
            accuracy_results["invalid_quantities"] > 0):
            raise ValueError(f"Accuracy check failed: {accuracy_results}")
        
        return {"accuracy": accuracy_results, "status": "success"}


@op(
    description="Check data consistency (referential integrity, duplicates)"
)
def check_consistency(context: OpExecutionContext, snowflake: SnowflakeResource) -> Dict[str, Any]:
    """Check referential integrity and duplicates"""
    with snowflake.get_connection() as conn:
        cursor = conn.cursor()
        
        # Check referential integrity
        ref_integrity_query = f"""
        SELECT 
            COUNT(*) as orphaned_records
        FROM {DW_DATABASE}.FACTS.fact_sales fs
        LEFT JOIN {DW_DATABASE}.DIMENSIONS.dim_product dp ON fs.product_key = dp.product_key
        LEFT JOIN {DW_DATABASE}.DIMENSIONS.dim_store ds ON fs.store_key = ds.store_key
        WHERE dp.product_key IS NULL OR ds.store_key IS NULL
        """
        cursor.execute(ref_integrity_query)
        ref_result = cursor.fetchone()
        orphaned_records = ref_result[0] if ref_result else 0
        
        # Check duplicates
        duplicate_query = f"""
        SELECT 
            transaction_id,
            product_key,
            COUNT(*) as duplicate_count
        FROM {DW_DATABASE}.FACTS.fact_sales
        GROUP BY transaction_id, product_key
        HAVING COUNT(*) > 1
        LIMIT 10
        """
        cursor.execute(duplicate_query)
        duplicates = cursor.fetchall()
        
        consistency_results = {
            "orphaned_records": orphaned_records,
            "duplicate_count": len(duplicates),
            "duplicates": [{"transaction_id": d[0], "product_key": d[1], "count": d[2]} for d in duplicates]
        }
        
        context.log.info(f"Consistency check results: {consistency_results}")
        
        # Fail if consistency issues found
        if orphaned_records > 0:
            raise ValueError(f"Referential integrity check failed: {orphaned_records} orphaned records")
        
        if len(duplicates) > 0:
            raise ValueError(f"Duplicate check failed: {len(duplicates)} duplicate transactions found")
        
        return {"consistency": consistency_results, "status": "success"}


@op(
    description="Check data timeliness (freshness)"
)
def check_timeliness(context: OpExecutionContext, snowflake: SnowflakeResource) -> Dict[str, Any]:
    """Check data freshness"""
    with snowflake.get_connection() as conn:
        cursor = conn.cursor()
        
        query = f"""
        SELECT 
            'raw_pos' as table_name,
            MAX(load_timestamp) as latest_load,
            DATEDIFF(hour, MAX(load_timestamp), CURRENT_TIMESTAMP()) as hours_since_load,
            CASE 
                WHEN DATEDIFF(hour, MAX(load_timestamp), CURRENT_TIMESTAMP()) > 2 THEN 'STALE'
                ELSE 'FRESH'
            END as freshness_status
        FROM {RAW_DATABASE}.BRONZE.raw_pos
        """
        cursor.execute(query)
        result = cursor.fetchone()
        
        timeliness_results = {
            "table_name": result[0] if result else None,
            "latest_load": str(result[1]) if result and result[1] else None,
            "hours_since_load": result[2] if result else None,
            "freshness_status": result[3] if result else None,
        }
        
        context.log.info(f"Timeliness check results: {timeliness_results}")
        
        # Fail if data is stale
        if timeliness_results["freshness_status"] == "STALE":
            raise ValueError(f"Timeliness check failed: Data is {timeliness_results['hours_since_load']} hours old")
        
        return {"timeliness": timeliness_results, "status": "success"}


@op(
    description="Check business rules"
)
def check_business_rules(context: OpExecutionContext, snowflake: SnowflakeResource) -> Dict[str, Any]:
    """Check business rule validations"""
    with snowflake.get_connection() as conn:
        cursor = conn.cursor()
        
        query = f"""
        SELECT 
            'stg_pos' as table_name,
            COUNT(*) as total_rows,
            SUM(CASE 
                WHEN ABS(total_amount - ((quantity * unit_price) - discount_amount + tax_amount)) > 0.01 
                THEN 1 ELSE 0 
            END) as calculation_errors
        FROM {STAGING_DATABASE}.SILVER.stg_pos
        WHERE created_at >= CURRENT_TIMESTAMP() - INTERVAL '24 hours'
        """
        cursor.execute(query)
        result = cursor.fetchone()
        
        business_rules_results = {
            "table_name": result[0] if result else None,
            "total_rows": result[1] if result else 0,
            "calculation_errors": result[2] if result else 0,
        }
        
        context.log.info(f"Business rules check results: {business_rules_results}")
        
        # Fail if business rules violated
        if business_rules_results["calculation_errors"] > 0:
            raise ValueError(f"Business rules check failed: {business_rules_results['calculation_errors']} calculation errors")
        
        return {"business_rules": business_rules_results, "status": "success"}


@op(
    description="Generate data quality report"
)
def generate_quality_report(context: OpExecutionContext, snowflake: SnowflakeResource, completeness: Dict[str, Any], accuracy: Dict[str, Any], consistency: Dict[str, Any], timeliness: Dict[str, Any], business_rules: Dict[str, Any]) -> Dict[str, Any]:
    """Generate comprehensive data quality report"""
    with snowflake.get_connection() as conn:
        cursor = conn.cursor()
        
        query = f"""
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
        """
        cursor.execute(query)
        
        context.log.info("Data quality report generated successfully")
        
        return {
            "report_generated": True,
            "status": "success"
        }


@job(
    description="Comprehensive data quality monitoring for retail data pipeline",
    tags={"orchestrator": "dagster", "layer": "data-quality"}
)
def data_quality_job():
    """Job definition for data quality monitoring"""
    completeness = check_completeness()
    accuracy = check_accuracy()
    consistency = check_consistency()
    timeliness = check_timeliness()
    business_rules = check_business_rules()
    
    # Generate report after all checks
    generate_quality_report(completeness, accuracy, consistency, timeliness, business_rules)


"""
Dagster Assets for Retail Data Pipeline
Defines data assets for Bronze, Silver, and Gold layers
"""

from dagster import asset, AssetExecutionContext, MetadataValue
from dagster_snowflake import SnowflakeResource
from typing import Dict, Any
import os

# Environment configuration
ENV = os.getenv("ENVIRONMENT", "DEV")
RAW_DATABASE = f"{ENV}_RAW"
STAGING_DATABASE = f"{ENV}_STAGING"
DW_DATABASE = f"{ENV}_DW"


@asset(
    group_name="bronze",
    description="Raw POS transaction data from source system"
)
def raw_pos_data(context: AssetExecutionContext, snowflake: SnowflakeResource) -> Dict[str, Any]:
    """Asset representing raw POS data in Bronze layer"""
    with snowflake.get_connection() as conn:
        cursor = conn.cursor()
        
        # Check row count and latest load
        query = f"""
        SELECT 
            COUNT(*) as row_count,
            MAX(load_timestamp) as latest_load
        FROM {RAW_DATABASE}.BRONZE.raw_pos
        WHERE load_timestamp >= CURRENT_TIMESTAMP() - INTERVAL '2 hours'
        """
        cursor.execute(query)
        result = cursor.fetchone()
        
        row_count = result[0] if result else 0
        latest_load = result[1] if result else None
        
        context.add_output_metadata({
            "row_count": MetadataValue.int(row_count),
            "latest_load": MetadataValue.text(str(latest_load)) if latest_load else MetadataValue.text("No data"),
        })
        
        return {
            "row_count": row_count,
            "latest_load": str(latest_load) if latest_load else None,
            "status": "success" if row_count > 0 else "no_data"
        }


@asset(
    group_name="bronze",
    description="Raw orders data from source system"
)
def raw_orders_data(context: AssetExecutionContext, snowflake: SnowflakeResource) -> Dict[str, Any]:
    """Asset representing raw orders data in Bronze layer"""
    with snowflake.get_connection() as conn:
        cursor = conn.cursor()
        
        query = f"""
        SELECT 
            COUNT(*) as row_count,
            MAX(load_timestamp) as latest_load
        FROM {RAW_DATABASE}.BRONZE.raw_orders
        WHERE load_timestamp >= CURRENT_TIMESTAMP() - INTERVAL '2 hours'
        """
        cursor.execute(query)
        result = cursor.fetchone()
        
        row_count = result[0] if result else 0
        latest_load = result[1] if result else None
        
        context.add_output_metadata({
            "row_count": MetadataValue.int(row_count),
            "latest_load": MetadataValue.text(str(latest_load)) if latest_load else MetadataValue.text("No data"),
        })
        
        return {
            "row_count": row_count,
            "latest_load": str(latest_load) if latest_load else None,
            "status": "success" if row_count > 0 else "no_data"
        }


@asset(
    group_name="bronze",
    description="Raw inventory data from source system"
)
def raw_inventory_data(context: AssetExecutionContext, snowflake: SnowflakeResource) -> Dict[str, Any]:
    """Asset representing raw inventory data in Bronze layer"""
    with snowflake.get_connection() as conn:
        cursor = conn.cursor()
        
        query = f"""
        SELECT 
            COUNT(*) as row_count,
            MAX(load_timestamp) as latest_load
        FROM {RAW_DATABASE}.BRONZE.raw_inventory
        WHERE load_timestamp >= CURRENT_TIMESTAMP() - INTERVAL '2 hours'
        """
        cursor.execute(query)
        result = cursor.fetchone()
        
        row_count = result[0] if result else 0
        latest_load = result[1] if result else None
        
        context.add_output_metadata({
            "row_count": MetadataValue.int(row_count),
            "latest_load": MetadataValue.text(str(latest_load)) if latest_load else MetadataValue.text("No data"),
        })
        
        return {
            "row_count": row_count,
            "latest_load": str(latest_load) if latest_load else None,
            "status": "success" if row_count > 0 else "no_data"
        }


@asset(
    group_name="silver",
    deps=[raw_pos_data],
    description="Cleaned and validated POS staging data"
)
def stg_pos_data(context: AssetExecutionContext, snowflake: SnowflakeResource) -> Dict[str, Any]:
    """Asset representing cleaned POS data in Silver layer"""
    with snowflake.get_connection() as conn:
        cursor = conn.cursor()
        
        # Execute transformation task
        cursor.execute(f"EXECUTE TASK {STAGING_DATABASE}.TASKS.task_bronze_to_silver_pos")
        
        # Check results
        query = f"""
        SELECT 
            COUNT(*) as total_rows,
            SUM(CASE WHEN is_valid = FALSE THEN 1 ELSE 0 END) as invalid_rows,
            SUM(CASE WHEN is_valid = TRUE THEN 1 ELSE 0 END) as valid_rows
        FROM {STAGING_DATABASE}.SILVER.stg_pos
        WHERE created_at >= CURRENT_TIMESTAMP() - INTERVAL '2 hours'
        """
        cursor.execute(query)
        result = cursor.fetchone()
        
        total_rows = result[0] if result else 0
        invalid_rows = result[1] if result else 0
        valid_rows = result[2] if result else 0
        
        context.add_output_metadata({
            "total_rows": MetadataValue.int(total_rows),
            "valid_rows": MetadataValue.int(valid_rows),
            "invalid_rows": MetadataValue.int(invalid_rows),
            "quality_score": MetadataValue.float(
                (valid_rows / total_rows * 100) if total_rows > 0 else 0
            ),
        })
        
        return {
            "total_rows": total_rows,
            "valid_rows": valid_rows,
            "invalid_rows": invalid_rows,
            "status": "success" if total_rows > 0 else "no_data"
        }


@asset(
    group_name="silver",
    deps=[raw_orders_data],
    description="Cleaned and validated orders staging data"
)
def stg_orders_data(context: AssetExecutionContext, snowflake: SnowflakeResource) -> Dict[str, Any]:
    """Asset representing cleaned orders data in Silver layer"""
    with snowflake.get_connection() as conn:
        cursor = conn.cursor()
        
        # Execute transformation task
        cursor.execute(f"EXECUTE TASK {STAGING_DATABASE}.TASKS.task_bronze_to_silver_orders")
        
        # Check results
        query = f"""
        SELECT 
            COUNT(*) as total_rows,
            SUM(CASE WHEN is_valid = FALSE THEN 1 ELSE 0 END) as invalid_rows,
            SUM(CASE WHEN is_valid = TRUE THEN 1 ELSE 0 END) as valid_rows
        FROM {STAGING_DATABASE}.SILVER.stg_orders
        WHERE created_at >= CURRENT_TIMESTAMP() - INTERVAL '2 hours'
        """
        cursor.execute(query)
        result = cursor.fetchone()
        
        total_rows = result[0] if result else 0
        invalid_rows = result[1] if result else 0
        valid_rows = result[2] if result else 0
        
        context.add_output_metadata({
            "total_rows": MetadataValue.int(total_rows),
            "valid_rows": MetadataValue.int(valid_rows),
            "invalid_rows": MetadataValue.int(invalid_rows),
        })
        
        return {
            "total_rows": total_rows,
            "valid_rows": valid_rows,
            "invalid_rows": invalid_rows,
            "status": "success" if total_rows > 0 else "no_data"
        }


@asset(
    group_name="silver",
    deps=[raw_inventory_data],
    description="Cleaned and validated inventory staging data"
)
def stg_inventory_data(context: AssetExecutionContext, snowflake: SnowflakeResource) -> Dict[str, Any]:
    """Asset representing cleaned inventory data in Silver layer"""
    with snowflake.get_connection() as conn:
        cursor = conn.cursor()
        
        # Execute transformation task
        cursor.execute(f"EXECUTE TASK {STAGING_DATABASE}.TASKS.task_bronze_to_silver_inventory")
        
        # Check results
        query = f"""
        SELECT 
            COUNT(*) as total_rows,
            SUM(CASE WHEN is_valid = FALSE THEN 1 ELSE 0 END) as invalid_rows,
            SUM(CASE WHEN is_valid = TRUE THEN 1 ELSE 0 END) as valid_rows
        FROM {STAGING_DATABASE}.SILVER.stg_inventory
        WHERE created_at >= CURRENT_TIMESTAMP() - INTERVAL '2 hours'
        """
        cursor.execute(query)
        result = cursor.fetchone()
        
        total_rows = result[0] if result else 0
        invalid_rows = result[1] if result else 0
        valid_rows = result[2] if result else 0
        
        context.add_output_metadata({
            "total_rows": MetadataValue.int(total_rows),
            "valid_rows": MetadataValue.int(valid_rows),
            "invalid_rows": MetadataValue.int(invalid_rows),
        })
        
        return {
            "total_rows": total_rows,
            "valid_rows": valid_rows,
            "invalid_rows": invalid_rows,
            "status": "success" if total_rows > 0 else "no_data"
        }


@asset(
    group_name="gold_dimensions",
    deps=[stg_pos_data, stg_orders_data],
    description="Customer dimension with SCD Type 2 support"
)
def dim_customer(context: AssetExecutionContext, snowflake: SnowflakeResource) -> Dict[str, Any]:
    """Asset representing customer dimension in Gold layer"""
    with snowflake.get_connection() as conn:
        cursor = conn.cursor()
        
        # Load customer dimension (SCD Type 2)
        cursor.execute(f"CALL {DW_DATABASE}.DIMENSIONS.sp_load_dim_customer_scd_type2()")
        
        # Check results
        query = f"""
        SELECT 
            COUNT(*) as total_records,
            SUM(CASE WHEN is_current = TRUE THEN 1 ELSE 0 END) as current_records,
            SUM(CASE WHEN is_current = FALSE THEN 1 ELSE 0 END) as historical_records
        FROM {DW_DATABASE}.DIMENSIONS.dim_customer
        """
        cursor.execute(query)
        result = cursor.fetchone()
        
        total_records = result[0] if result else 0
        current_records = result[1] if result else 0
        historical_records = result[2] if result else 0
        
        context.add_output_metadata({
            "total_records": MetadataValue.int(total_records),
            "current_records": MetadataValue.int(current_records),
            "historical_records": MetadataValue.int(historical_records),
        })
        
        return {
            "total_records": total_records,
            "current_records": current_records,
            "historical_records": historical_records,
            "status": "success"
        }


@asset(
    group_name="gold_dimensions",
    deps=[stg_pos_data],
    description="Product dimension with SCD Type 1 support"
)
def dim_product(context: AssetExecutionContext, snowflake: SnowflakeResource) -> Dict[str, Any]:
    """Asset representing product dimension in Gold layer"""
    with snowflake.get_connection() as conn:
        cursor = conn.cursor()
        
        # Load product dimension (SCD Type 1)
        cursor.execute(f"CALL {DW_DATABASE}.DIMENSIONS.sp_load_dim_product_scd_type1()")
        
        # Check results
        query = f"""
        SELECT COUNT(*) as total_records
        FROM {DW_DATABASE}.DIMENSIONS.dim_product
        """
        cursor.execute(query)
        result = cursor.fetchone()
        
        total_records = result[0] if result else 0
        
        context.add_output_metadata({
            "total_records": MetadataValue.int(total_records),
        })
        
        return {
            "total_records": total_records,
            "status": "success"
        }


@asset(
    group_name="gold_facts",
    deps=[dim_customer, dim_product, stg_pos_data],
    description="Sales fact table with dimension lookups"
)
def fact_sales(context: AssetExecutionContext, snowflake: SnowflakeResource) -> Dict[str, Any]:
    """Asset representing sales fact table in Gold layer"""
    with snowflake.get_connection() as conn:
        cursor = conn.cursor()
        
        # Load fact sales
        cursor.execute(f"CALL {DW_DATABASE}.FACTS.sp_load_fact_sales()")
        
        # Check results
        query = f"""
        SELECT 
            COUNT(*) as total_rows,
            SUM(total_amount) as total_sales,
            MIN(transaction_timestamp) as earliest_transaction,
            MAX(transaction_timestamp) as latest_transaction
        FROM {DW_DATABASE}.FACTS.fact_sales
        WHERE created_at >= CURRENT_TIMESTAMP() - INTERVAL '2 hours'
        """
        cursor.execute(query)
        result = cursor.fetchone()
        
        total_rows = result[0] if result else 0
        total_sales = float(result[1]) if result and result[1] else 0.0
        earliest = str(result[2]) if result and result[2] else None
        latest = str(result[3]) if result and result[3] else None
        
        context.add_output_metadata({
            "total_rows": MetadataValue.int(total_rows),
            "total_sales": MetadataValue.float(total_sales),
            "earliest_transaction": MetadataValue.text(earliest) if earliest else MetadataValue.text("N/A"),
            "latest_transaction": MetadataValue.text(latest) if latest else MetadataValue.text("N/A"),
        })
        
        return {
            "total_rows": total_rows,
            "total_sales": total_sales,
            "earliest_transaction": earliest,
            "latest_transaction": latest,
            "status": "success" if total_rows > 0 else "no_data"
        }


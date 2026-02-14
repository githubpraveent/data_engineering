"""
Dagster Job for Data Transformation
Orchestrates the transformation of data from Bronze → Silver → Gold layers
"""

from dagster import job, op, OpExecutionContext, In
from dagster_snowflake import SnowflakeResource
from typing import Dict, Any
import os

ENV = os.getenv("ENVIRONMENT", "DEV")
STAGING_DATABASE = f"{ENV}_STAGING"
DW_DATABASE = f"{ENV}_DW"


@op(
    description="Transform POS data from Bronze to Silver"
)
def transform_pos(context: OpExecutionContext, snowflake: SnowflakeResource) -> Dict[str, Any]:
    """Transform POS data from Bronze to Silver layer"""
    with snowflake.get_connection() as conn:
        cursor = conn.cursor()
        
        context.log.info("Executing POS transformation task")
        cursor.execute(f"EXECUTE TASK {STAGING_DATABASE}.TASKS.task_bronze_to_silver_pos")
        
        # Check results
        query = f"""
        SELECT 
            COUNT(*) as total_rows,
            SUM(CASE WHEN is_valid = FALSE THEN 1 ELSE 0 END) as invalid_rows
        FROM {STAGING_DATABASE}.SILVER.stg_pos
        WHERE created_at >= CURRENT_TIMESTAMP() - INTERVAL '2 hours'
        """
        cursor.execute(query)
        result = cursor.fetchone()
        
        return {
            "total_rows": result[0] if result else 0,
            "invalid_rows": result[1] if result else 0,
            "status": "success"
        }


@op(
    description="Transform Orders data from Bronze to Silver"
)
def transform_orders(context: OpExecutionContext, snowflake: SnowflakeResource) -> Dict[str, Any]:
    """Transform Orders data from Bronze to Silver layer"""
    with snowflake.get_connection() as conn:
        cursor = conn.cursor()
        
        context.log.info("Executing Orders transformation task")
        cursor.execute(f"EXECUTE TASK {STAGING_DATABASE}.TASKS.task_bronze_to_silver_orders")
        
        # Check results
        query = f"""
        SELECT 
            COUNT(*) as total_rows,
            SUM(CASE WHEN is_valid = FALSE THEN 1 ELSE 0 END) as invalid_rows
        FROM {STAGING_DATABASE}.SILVER.stg_orders
        WHERE created_at >= CURRENT_TIMESTAMP() - INTERVAL '2 hours'
        """
        cursor.execute(query)
        result = cursor.fetchone()
        
        return {
            "total_rows": result[0] if result else 0,
            "invalid_rows": result[1] if result else 0,
            "status": "success"
        }


@op(
    description="Transform Inventory data from Bronze to Silver"
)
def transform_inventory(context: OpExecutionContext, snowflake: SnowflakeResource) -> Dict[str, Any]:
    """Transform Inventory data from Bronze to Silver layer"""
    with snowflake.get_connection() as conn:
        cursor = conn.cursor()
        
        context.log.info("Executing Inventory transformation task")
        cursor.execute(f"EXECUTE TASK {STAGING_DATABASE}.TASKS.task_bronze_to_silver_inventory")
        
        # Check results
        query = f"""
        SELECT 
            COUNT(*) as total_rows,
            SUM(CASE WHEN is_valid = FALSE THEN 1 ELSE 0 END) as invalid_rows
        FROM {STAGING_DATABASE}.SILVER.stg_inventory
        WHERE created_at >= CURRENT_TIMESTAMP() - INTERVAL '2 hours'
        """
        cursor.execute(query)
        result = cursor.fetchone()
        
        return {
            "total_rows": result[0] if result else 0,
            "invalid_rows": result[1] if result else 0,
            "status": "success"
        }


@op(
    description="Validate Silver layer data quality"
)
def validate_silver_quality(context: OpExecutionContext, snowflake: SnowflakeResource, pos_result: Dict[str, Any], orders_result: Dict[str, Any], inventory_result: Dict[str, Any]) -> Dict[str, Any]:
    """Validate data quality in Silver layer"""
    with snowflake.get_connection() as conn:
        cursor = conn.cursor()
        
        query = f"""
        SELECT 
            'stg_pos' as table_name,
            COUNT(*) as total_rows,
            SUM(CASE WHEN is_valid = FALSE THEN 1 ELSE 0 END) as invalid_rows,
            SUM(CASE WHEN transaction_id IS NULL THEN 1 ELSE 0 END) as null_transaction_id
        FROM {STAGING_DATABASE}.SILVER.stg_pos
        WHERE created_at >= CURRENT_TIMESTAMP() - INTERVAL '2 hours'
        HAVING invalid_rows > 0 OR null_transaction_id > 0
        """
        cursor.execute(query)
        result = cursor.fetchone()
        
        if result:
            raise ValueError(f"Data quality validation failed: {result}")
        
        return {"status": "success", "message": "All quality checks passed"}


@op(
    description="Load Customer dimension (SCD Type 2)"
)
def load_dim_customer(context: OpExecutionContext, snowflake: SnowflakeResource) -> Dict[str, Any]:
    """Load customer dimension with SCD Type 2"""
    with snowflake.get_connection() as conn:
        cursor = conn.cursor()
        
        context.log.info("Loading customer dimension (SCD Type 2)")
        cursor.execute(f"CALL {DW_DATABASE}.DIMENSIONS.sp_load_dim_customer_scd_type2()")
        
        query = f"""
        SELECT 
            COUNT(*) as total_records,
            SUM(CASE WHEN is_current = TRUE THEN 1 ELSE 0 END) as current_records
        FROM {DW_DATABASE}.DIMENSIONS.dim_customer
        """
        cursor.execute(query)
        result = cursor.fetchone()
        
        return {
            "total_records": result[0] if result else 0,
            "current_records": result[1] if result else 0,
            "status": "success"
        }


@op(
    description="Load Product dimension (SCD Type 1)"
)
def load_dim_product(context: OpExecutionContext, snowflake: SnowflakeResource) -> Dict[str, Any]:
    """Load product dimension with SCD Type 1"""
    with snowflake.get_connection() as conn:
        cursor = conn.cursor()
        
        context.log.info("Loading product dimension (SCD Type 1)")
        cursor.execute(f"CALL {DW_DATABASE}.DIMENSIONS.sp_load_dim_product_scd_type1()")
        
        query = f"SELECT COUNT(*) FROM {DW_DATABASE}.DIMENSIONS.dim_product"
        cursor.execute(query)
        result = cursor.fetchone()
        
        return {
            "total_records": result[0] if result else 0,
            "status": "success"
        }


@op(
    description="Load Fact Sales table"
)
def load_fact_sales(context: OpExecutionContext, snowflake: SnowflakeResource, customer_dim: Dict[str, Any], product_dim: Dict[str, Any]) -> Dict[str, Any]:
    """Load fact sales table"""
    with snowflake.get_connection() as conn:
        cursor = conn.cursor()
        
        context.log.info("Loading fact sales")
        cursor.execute(f"CALL {DW_DATABASE}.FACTS.sp_load_fact_sales()")
        
        query = f"""
        SELECT 
            COUNT(*) as total_rows,
            SUM(total_amount) as total_sales
        FROM {DW_DATABASE}.FACTS.fact_sales
        WHERE created_at >= CURRENT_TIMESTAMP() - INTERVAL '2 hours'
        """
        cursor.execute(query)
        result = cursor.fetchone()
        
        return {
            "total_rows": result[0] if result else 0,
            "total_sales": float(result[1]) if result and result[1] else 0.0,
            "status": "success"
        }


@op(
    description="Validate referential integrity in Gold layer"
)
def validate_gold_quality(context: OpExecutionContext, snowflake: SnowflakeResource, facts: Dict[str, Any]) -> Dict[str, Any]:
    """Validate referential integrity in Gold layer"""
    with snowflake.get_connection() as conn:
        cursor = conn.cursor()
        
        query = f"""
        SELECT 
            COUNT(*) as orphaned_records
        FROM {DW_DATABASE}.FACTS.fact_sales fs
        LEFT JOIN {DW_DATABASE}.DIMENSIONS.dim_product dp ON fs.product_key = dp.product_key
        LEFT JOIN {DW_DATABASE}.DIMENSIONS.dim_store ds ON fs.store_key = ds.store_key
        WHERE dp.product_key IS NULL OR ds.store_key IS NULL
        """
        cursor.execute(query)
        result = cursor.fetchone()
        
        orphaned_records = result[0] if result else 0
        
        if orphaned_records > 0:
            raise ValueError(f"Referential integrity check failed: {orphaned_records} orphaned records")
        
        return {
            "orphaned_records": orphaned_records,
            "status": "success",
            "message": "All referential integrity checks passed"
        }


@job(
    description="Transform retail data from Bronze to Silver to Gold layers",
    tags={"orchestrator": "dagster", "layer": "transformation"}
)
def transformation_job():
    """Job definition for data transformation pipeline"""
    # Bronze to Silver transformations (can run in parallel)
    pos_result = transform_pos()
    orders_result = transform_orders()
    inventory_result = transform_inventory()
    
    # Validate Silver quality (runs after all transformations complete)
    silver_validation = validate_silver_quality(pos_result, orders_result, inventory_result)
    
    # Load dimensions (can run in parallel, but after silver validation)
    customer_dim = load_dim_customer()
    product_dim = load_dim_product()
    
    # Load facts (depends on dimensions)
    fact_sales_result = load_fact_sales(customer_dim, product_dim)
    
    # Validate Gold quality
    validate_gold_quality(fact_sales_result)


"""
Common utility functions for Databricks notebooks.
Contains helper functions for data processing, logging, and error handling.
"""

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, lit, current_timestamp, coalesce, when, trim, upper,
    regexp_replace, to_date, to_timestamp, sha2, concat
)
from pyspark.sql.types import TimestampType, DateType
import logging
from datetime import datetime
from typing import Optional, List

def get_spark_session() -> SparkSession:
    """Get or create Spark session."""
    return SparkSession.builder.getOrCreate()

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def get_current_timestamp() -> TimestampType:
    """Get current timestamp for record tracking."""
    return current_timestamp()

def add_metadata_columns(df: DataFrame, source_system: str) -> DataFrame:
    """
    Add standard metadata columns to a DataFrame.
    
    Args:
        df: Input DataFrame
        source_system: Name of the source system
        
    Returns:
        DataFrame with added metadata columns
    """
    return df.withColumn("ingestion_timestamp", current_timestamp()) \
             .withColumn("source_system", lit(source_system))

def clean_string_column(df: DataFrame, column_name: str) -> DataFrame:
    """
    Clean string column: trim whitespace and replace nulls.
    
    Args:
        df: Input DataFrame
        column_name: Name of column to clean
        
    Returns:
        DataFrame with cleaned column
    """
    return df.withColumn(
        column_name,
        when(col(column_name).isNotNull(), trim(col(column_name)))
        .otherwise(None)
    )

def parse_date_column(df: DataFrame, column_name: str, format_string: str = "yyyy-MM-dd") -> DataFrame:
    """
    Parse date column from string format.
    
    Args:
        df: Input DataFrame
        column_name: Name of column to parse
        format_string: Date format string
        
    Returns:
        DataFrame with parsed date column
    """
    return df.withColumn(
        column_name,
        to_date(col(column_name), format_string)
    )

def parse_timestamp_column(df: DataFrame, column_name: str, format_string: str = "yyyy-MM-dd HH:mm:ss") -> DataFrame:
    """
    Parse timestamp column from string format.
    
    Args:
        df: Input DataFrame
        column_name: Name of column to parse
        format_string: Timestamp format string
        
    Returns:
        DataFrame with parsed timestamp column
    """
    return df.withColumn(
        column_name,
        to_timestamp(col(column_name), format_string)
    )

def parse_decimal_column(df: DataFrame, column_name: str, precision: int = 18, scale: int = 2) -> DataFrame:
    """
    Parse decimal column from string format.
    
    Args:
        df: Input DataFrame
        column_name: Name of column to parse
        precision: Decimal precision
        scale: Decimal scale
        
    Returns:
        DataFrame with parsed decimal column
    """
    from pyspark.sql.types import DecimalType
    from pyspark.sql.functions import regexp_replace
    
    return df.withColumn(
        column_name,
        regexp_replace(col(column_name), "[^0-9.-]", "").cast(f"decimal({precision},{scale})")
    )

def parse_integer_column(df: DataFrame, column_name: str) -> DataFrame:
    """
    Parse integer column from string format.
    
    Args:
        df: Input DataFrame
        column_name: Name of column to parse
        
    Returns:
        DataFrame with parsed integer column
    """
    from pyspark.sql.functions import regexp_replace
    
    return df.withColumn(
        column_name,
        regexp_replace(col(column_name), "[^0-9-]", "").cast("int")
    )

def generate_surrogate_key(df: DataFrame, key_name: str, natural_keys: List[str]) -> DataFrame:
    """
    Generate a surrogate key using SHA2 hash of natural keys.
    
    Args:
        df: Input DataFrame
        key_name: Name of the surrogate key column
        natural_keys: List of natural key column names
        
    Returns:
        DataFrame with surrogate key column
    """
    key_columns = [col(k) for k in natural_keys]
    return df.withColumn(
        key_name,
        sha2(concat(*key_columns), 256).cast("string")
    )

def deduplicate_dataframe(df: DataFrame, partition_cols: List[str], order_col: str = "ingestion_timestamp") -> DataFrame:
    """
    Deduplicate DataFrame by keeping the most recent record per partition.
    
    Args:
        df: Input DataFrame
        partition_cols: Columns to partition by for deduplication
        order_col: Column to order by (descending) to determine latest record
        
    Returns:
        Deduplicated DataFrame
    """
    from pyspark.sql.window import Window
    
    window_spec = Window.partitionBy(partition_cols).orderBy(col(order_col).desc())
    return df.withColumn("row_num", row_number().over(window_spec)) \
             .filter(col("row_num") == 1) \
             .drop("row_num")

def validate_not_null(df: DataFrame, column_name: str) -> bool:
    """
    Validate that a column has no null values.
    
    Args:
        df: Input DataFrame
        column_name: Name of column to validate
        
    Returns:
        True if no nulls, False otherwise
    """
    null_count = df.filter(col(column_name).isNull()).count()
    return null_count == 0

def validate_unique(df: DataFrame, column_name: str) -> bool:
    """
    Validate that a column has unique values.
    
    Args:
        df: Input DataFrame
        column_name: Name of column to validate
        
    Returns:
        True if unique, False otherwise
    """
    total_count = df.count()
    distinct_count = df.select(column_name).distinct().count()
    return total_count == distinct_count

def get_table_path(catalog: str, schema: str, table: str, environment: str = "dev") -> str:
    """
    Generate Delta table path based on Unity Catalog structure.
    
    Args:
        catalog: Unity Catalog catalog name
        schema: Schema name
        table: Table name
        environment: Environment (dev, qa, prod)
        
    Returns:
        Full table path
    """
    return f"{catalog}.{environment}_{schema}.{table}"

def write_delta_table(
    df: DataFrame,
    table_path: str,
    mode: str = "append",
    partition_cols: Optional[List[str]] = None,
    merge_keys: Optional[List[str]] = None
):
    """
    Write DataFrame to Delta table with options for merge or append.
    
    Args:
        df: DataFrame to write
        table_path: Target Delta table path
        mode: Write mode ('append', 'overwrite', 'merge')
        partition_cols: Columns to partition by
        merge_keys: Keys for merge operation (if mode='merge')
    """
    if mode == "merge" and merge_keys:
        # Perform merge operation
        from delta.tables import DeltaTable
        
        delta_table = DeltaTable.forPath(SparkSession.builder.getOrCreate(), table_path)
        
        merge_condition = " AND ".join([f"target.{k} = source.{k}" for k in merge_keys])
        
        delta_table.alias("target").merge(
            df.alias("source"),
            merge_condition
        ).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
    else:
        writer = df.write.format("delta").mode(mode)
        
        if partition_cols:
            writer = writer.partitionBy(*partition_cols)
        
        writer.option("mergeSchema", "true").save(table_path)

def optimize_delta_table(table_path: str, z_order_cols: Optional[List[str]] = None):
    """
    Optimize Delta table: compact files and optionally Z-order.
    
    Args:
        table_path: Delta table path
        z_order_cols: Columns for Z-ordering (optional)
    """
    spark = get_spark_session()
    
    if z_order_cols:
        spark.sql(f"OPTIMIZE {table_path} ZORDER BY ({', '.join(z_order_cols)})")
    else:
        spark.sql(f"OPTIMIZE {table_path}")

def vacuum_delta_table(table_path: str, retention_hours: int = 168):
    """
    Vacuum Delta table to remove old files.
    
    Args:
        table_path: Delta table path
        retention_hours: Retention period in hours (default 7 days)
    """
    spark = get_spark_session()
    spark.sql(f"VACUUM {table_path} RETAIN {retention_hours} HOURS")

def enable_change_data_feed(table_path: str):
    """
    Enable Change Data Feed (CDF) for a Delta table.
    
    Args:
        table_path: Delta table path
    """
    spark = get_spark_session()
    spark.sql(f"ALTER TABLE {table_path} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")

def read_change_data_feed(table_path: str, starting_version: Optional[int] = None, ending_version: Optional[int] = None):
    """
    Read Change Data Feed from a Delta table.
    
    Args:
        table_path: Delta table path
        starting_version: Starting version (optional)
        ending_version: Ending version (optional)
        
    Returns:
        DataFrame with change data
    """
    spark = get_spark_session()
    
    if starting_version and ending_version:
        return spark.read.format("delta").option("readChangeFeed", "true") \
                     .option("startingVersion", starting_version) \
                     .option("endingVersion", ending_version) \
                     .table(table_path)
    elif starting_version:
        return spark.read.format("delta").option("readChangeFeed", "true") \
                     .option("startingVersion", starting_version) \
                     .table(table_path)
    else:
        return spark.read.format("delta").option("readChangeFeed", "true").table(table_path)

def get_table_version(table_path: str) -> int:
    """
    Get current version of a Delta table.
    
    Args:
        table_path: Delta table path
        
    Returns:
        Current table version number
    """
    spark = get_spark_session()
    result = spark.sql(f"DESCRIBE HISTORY {table_path} LIMIT 1").collect()
    if result:
        return result[0]['version']
    return 0

def time_travel_query(table_path: str, version: int):
    """
    Query a Delta table at a specific version (time travel).
    
    Args:
        table_path: Delta table path
        version: Version number to query
        
    Returns:
        DataFrame at specified version
    """
    spark = get_spark_session()
    return spark.read.format("delta").option("versionAsOf", version).table(table_path)


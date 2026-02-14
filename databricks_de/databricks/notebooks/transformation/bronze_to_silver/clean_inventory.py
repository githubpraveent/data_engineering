"""
Databricks Notebook: Bronze to Silver - Inventory
Transforms raw inventory data from Bronze to cleaned Silver layer.
"""

# MAGIC %md
# MAGIC # Bronze to Silver Transformation: Inventory

# COMMAND ----------

# MAGIC %run ../../utilities/common_functions
# MAGIC %run ../../utilities/schema_definitions

# COMMAND ----------

# Configuration
dbutils.widgets.text("environment", "dev", "Environment")
dbutils.widgets.text("catalog", "retail_datalake", "Unity Catalog")
dbutils.widgets.text("bronze_schema", "bronze", "Bronze Schema Name")
dbutils.widgets.text("silver_schema", "silver", "Silver Schema Name")
dbutils.widgets.text("incremental", "true", "Incremental Load")

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, lit, current_timestamp, trim, coalesce, when, to_timestamp, regexp_replace
)
from pyspark.sql.types import DecimalType, IntegerType
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number
from delta.tables import DeltaTable
import logging

spark = SparkSession.builder.getOrCreate()
logger = setup_logging()

ENVIRONMENT = dbutils.widgets.get("environment")
CATALOG = dbutils.widgets.get("catalog")
BRONZE_SCHEMA = dbutils.widgets.get("bronze_schema")
SILVER_SCHEMA = dbutils.widgets.get("silver_schema")

BRONZE_TABLE = f"{CATALOG}.{ENVIRONMENT}_{BRONZE_SCHEMA}.inventory"
SILVER_TABLE = f"{CATALOG}.{ENVIRONMENT}_{SILVER_SCHEMA}.inventory"

logger.info(f"Starting Bronze to Silver transformation for Inventory")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Read from Bronze

# COMMAND ----------

df_bronze = spark.read.format("delta").table(BRONZE_TABLE)
record_count = df_bronze.count()
logger.info(f"Read {record_count} records from Bronze")

if record_count == 0:
    dbutils.notebook.exit("SUCCESS: No records to process")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Clean and Transform

# COMMAND ----------

df_silver = df_bronze \
    # Clean string fields
    .withColumn("product_id", trim(col("product_id"))) \
    .withColumn("store_id", trim(col("store_id"))) \
    \
    # Convert integer columns
    .withColumn("quantity_on_hand", 
                regexp_replace(col("quantity_on_hand"), "[^0-9-]", "").cast(IntegerType())) \
    .withColumn("quantity_reserved", 
                regexp_replace(col("quantity_reserved"), "[^0-9-]", "").cast(IntegerType())) \
    .withColumn("reorder_level", 
                regexp_replace(col("reorder_level"), "[^0-9-]", "").cast(IntegerType())) \
    \
    # Convert decimal columns
    .withColumn("unit_cost", 
                regexp_replace(col("unit_cost"), "[^0-9.-]", "").cast(DecimalType(18, 2))) \
    \
    # Convert timestamp
    .withColumn("last_updated", 
                coalesce(
                    to_timestamp(col("last_updated"), "yyyy-MM-dd HH:mm:ss"),
                    to_timestamp(col("last_updated"), "yyyy-MM-dd"),
                    current_timestamp()
                )) \
    \
    # Calculate available quantity
    .withColumn("quantity_available", 
                coalesce(col("quantity_on_hand"), lit(0)) - 
                coalesce(col("quantity_reserved"), lit(0))) \
    \
    # Handle nulls
    .withColumn("quantity_on_hand", coalesce(col("quantity_on_hand"), lit(0))) \
    .withColumn("quantity_reserved", coalesce(col("quantity_reserved"), lit(0))) \
    .withColumn("quantity_available", coalesce(col("quantity_available"), lit(0))) \
    \
    # Select columns
    .select(
        col("product_id"),
        col("store_id"),
        col("quantity_on_hand"),
        col("quantity_reserved"),
        col("quantity_available"),
        col("reorder_level"),
        col("unit_cost"),
        col("last_updated"),
        col("source_system"),
        current_timestamp().alias("created_at"),
        current_timestamp().alias("updated_at"),
        lit(True).alias("is_current"),
        lit(1).alias("version")
    )

logger.info("Data cleaning completed")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Validate

# COMMAND ----------

initial_count = df_silver.count()
df_silver = df_silver.filter(
    col("product_id").isNotNull() & 
    col("store_id").isNotNull() &
    col("quantity_available").isNotNull()
)
final_count = df_silver.count()

logger.info(f"Validation: {initial_count} → {final_count} records")

if final_count == 0:
    dbutils.notebook.exit("WARNING: No valid records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Deduplicate

# COMMAND ----------

window_spec = Window.partitionBy("product_id", "store_id").orderBy(col("created_at").desc())
df_silver = df_silver.withColumn("row_num", row_number().over(window_spec)) \
                     .filter(col("row_num") == 1) \
                     .drop("row_num")

dedup_count = df_silver.count()
logger.info(f"After deduplication: {dedup_count} records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Merge to Silver

# COMMAND ----------

spark.sql(f"CREATE DATABASE IF NOT EXISTS {CATALOG}.{ENVIRONMENT}_{SILVER_SCHEMA}")

try:
    silver_table = DeltaTable.forPath(spark, SILVER_TABLE)
    merge_condition = "target.product_id = source.product_id AND target.store_id = source.store_id"
    silver_table.alias("target").merge(
        df_silver.alias("source"),
        merge_condition
    ).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
    logger.info("Merged to Silver table")
except:
    df_silver.write.format("delta").mode("overwrite").option("mergeSchema", "true").saveAsTable(SILVER_TABLE)
    logger.info(f"Created new Silver table: {SILVER_TABLE}")

# COMMAND ----------

try:
    spark.sql(f"ALTER TABLE {SILVER_TABLE} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")
    logger.info("CDF enabled")
except Exception as e:
    logger.warning(f"Could not enable CDF: {e}")

# COMMAND ----------

final_count = spark.read.format("delta").table(SILVER_TABLE).count()
logger.info(f"Transformation completed: {final_count} total records")

dbutils.notebook.exit(f"SUCCESS: {dedup_count} records processed, {final_count} total in Silver")


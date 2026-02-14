"""
Databricks Notebook: Bronze to Silver - Orders
Transforms raw orders data from Bronze to cleaned, validated Silver layer.
"""

# MAGIC %md
# MAGIC # Bronze to Silver Transformation: Orders
# MAGIC 
# MAGIC This notebook cleans, validates, and transforms orders data from Bronze to Silver layer.
# MAGIC - Data type conversion
# MAGIC - Data cleaning and validation
# MAGIC - Deduplication
# MAGIC - Schema normalization

# COMMAND ----------

# MAGIC %run ../../utilities/common_functions
# MAGIC %run ../../utilities/schema_definitions

# COMMAND ----------

# Configuration
dbutils.widgets.text("environment", "dev", "Environment")
dbutils.widgets.text("catalog", "retail_datalake", "Unity Catalog")
dbutils.widgets.text("bronze_schema", "bronze", "Bronze Schema Name")
dbutils.widgets.text("silver_schema", "silver", "Silver Schema Name")
dbutils.widgets.text("incremental", "true", "Incremental Load (true/false)")
dbutils.widgets.text("last_processed_timestamp", "", "Last Processed Timestamp (for incremental)")

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, lit, current_timestamp, coalesce, when, trim, upper,
    to_date, to_timestamp, cast, concat
)
from pyspark.sql.types import DecimalType, DateType, TimestampType
import logging

spark = SparkSession.builder.getOrCreate()
logger = setup_logging()

# Get parameters
ENVIRONMENT = dbutils.widgets.get("environment")
CATALOG = dbutils.widgets.get("catalog")
BRONZE_SCHEMA = dbutils.widgets.get("bronze_schema")
SILVER_SCHEMA = dbutils.widgets.get("silver_schema")
INCREMENTAL = dbutils.widgets.get("incremental").lower() == "true"
LAST_PROCESSED = dbutils.widgets.get("last_processed_timestamp")

# Table paths
BRONZE_TABLE = f"{CATALOG}.{ENVIRONMENT}_{BRONZE_SCHEMA}.orders"
SILVER_TABLE = f"{CATALOG}.{ENVIRONMENT}_{SILVER_SCHEMA}.orders"

logger.info(f"Starting Bronze to Silver transformation for Orders")
logger.info(f"Source: {BRONZE_TABLE}, Target: {SILVER_TABLE}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Read from Bronze Layer

# COMMAND ----------

# Read from Bronze table
if INCREMENTAL and LAST_PROCESSED:
    df_bronze = spark.read.format("delta").table(BRONZE_TABLE) \
        .filter(col("ingestion_timestamp") > LAST_PROCESSED)
    logger.info(f"Incremental load: reading records after {LAST_PROCESSED}")
else:
    df_bronze = spark.read.format("delta").table(BRONZE_TABLE)
    logger.info("Full load: reading all records from Bronze")

record_count = df_bronze.count()
logger.info(f"Read {record_count} records from Bronze")

if record_count == 0:
    logger.warning("No new records to process")
    dbutils.notebook.exit("SUCCESS: No new records to process")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Data Type Conversion and Cleaning

# COMMAND ----------

df_silver = df_bronze \
    # Clean string columns
    .withColumn("order_id", trim(col("order_id"))) \
    .withColumn("customer_id", trim(col("customer_id"))) \
    .withColumn("order_status", upper(trim(col("order_status")))) \
    .withColumn("currency", upper(trim(col("currency")))) \
    .withColumn("store_id", trim(col("store_id"))) \
    .withColumn("payment_method", trim(col("payment_method"))) \
    \
    # Convert date columns
    .withColumn("order_date", 
                coalesce(
                    to_date(col("order_date"), "yyyy-MM-dd"),
                    to_date(col("order_date"), "MM/dd/yyyy"),
                    to_date(col("order_date"), "dd-MM-yyyy")
                )) \
    \
    # Create order_timestamp from order_date (default to 00:00:00)
    .withColumn("order_timestamp", 
                when(col("order_date").isNotNull(),
                     to_timestamp(concat(col("order_date"), lit(" 00:00:00"))))
                .otherwise(col("ingestion_timestamp"))) \
    \
    # Convert numeric columns (handle string to decimal conversion)
    .withColumn("total_amount", 
                regexp_replace(col("total_amount"), "[^0-9.-]", "").cast(DecimalType(18, 2))) \
    \
    # Standardize order status
    .withColumn("order_status", 
                when(col("order_status").isin(["COMPLETED", "COMPLETE"]), "COMPLETED")
                .when(col("order_status").isin(["PENDING", "PROCESSING"]), "PENDING")
                .when(col("order_status").isin(["CANCELLED", "CANCEL"]), "CANCELLED")
                .otherwise(col("order_status"))) \
    \
    # Handle nulls with defaults
    .withColumn("currency", coalesce(col("currency"), lit("USD"))) \
    .withColumn("order_status", coalesce(col("order_status"), lit("UNKNOWN"))) \
    \
    # Select and rename columns to match Silver schema
    .select(
        col("order_id"),
        col("customer_id"),
        col("order_date"),
        col("order_timestamp"),
        col("order_status"),
        col("total_amount"),
        col("currency"),
        col("store_id"),
        col("payment_method"),
        col("source_system"),
        current_timestamp().alias("created_at"),
        current_timestamp().alias("updated_at"),
        lit(True).alias("is_current"),
        lit(1).alias("version")
    )

logger.info("Data cleaning and transformation completed")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Data Validation

# COMMAND ----------

# Validate required fields
initial_count = df_silver.count()

# Remove records with null order_id
df_silver = df_silver.filter(col("order_id").isNotNull())

# Remove records with invalid order_date
df_silver = df_silver.filter(col("order_date").isNotNull())

# Remove records with invalid total_amount
df_silver = df_silver.filter(col("total_amount").isNotNull() & (col("total_amount") >= 0))

final_count = df_silver.count()
filtered_count = initial_count - final_count

logger.info(f"Validation: {initial_count} records → {final_count} valid records ({filtered_count} filtered)")

if final_count == 0:
    logger.warning("No valid records after validation")
    dbutils.notebook.exit("WARNING: No valid records after validation")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Deduplication

# COMMAND ----------

from pyspark.sql.window import Window

# Deduplicate based on order_id, keeping the latest ingestion
window_spec = Window.partitionBy("order_id").orderBy(col("created_at").desc())

df_silver = df_silver.withColumn("row_num", row_number().over(window_spec)) \
                     .filter(col("row_num") == 1) \
                     .drop("row_num")

dedup_count = df_silver.count()
logger.info(f"After deduplication: {dedup_count} records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Merge to Silver Table (Delta MERGE)

# COMMAND ----------

from delta.tables import DeltaTable

# Create Silver schema/database if not exists
spark.sql(f"CREATE DATABASE IF NOT EXISTS {CATALOG}.{ENVIRONMENT}_{SILVER_SCHEMA}")

# Check if Silver table exists
try:
    silver_table = DeltaTable.forPath(spark, SILVER_TABLE)
    table_exists = True
except:
    # Create table with first batch
    df_silver.write \
        .format("delta") \
        .mode("overwrite") \
        .option("mergeSchema", "true") \
        .saveAsTable(SILVER_TABLE)
    logger.info(f"Created new Silver table: {SILVER_TABLE}")
    table_exists = False

if table_exists:
    # Perform MERGE operation (upsert)
    merge_condition = "target.order_id = source.order_id"
    
    silver_table = DeltaTable.forPath(spark, SILVER_TABLE)
    
    silver_table.alias("target").merge(
        df_silver.alias("source"),
        merge_condition
    ).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
    
    logger.info("Merged records to Silver table")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6: Enable Change Data Feed

# COMMAND ----------

try:
    spark.sql(f"ALTER TABLE {SILVER_TABLE} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")
    logger.info("Change Data Feed enabled for Silver table")
except Exception as e:
    logger.warning(f"Could not enable CDF: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 7: Optimize Table

# COMMAND ----------

# Optimize Silver table for better query performance
try:
    spark.sql(f"OPTIMIZE {SILVER_TABLE}")
    logger.info("Table optimized")
except Exception as e:
    logger.warning(f"Could not optimize table: {e}")

# COMMAND ----------

final_record_count = spark.read.format("delta").table(SILVER_TABLE).count()
logger.info(f"Transformation completed: {final_record_count} total records in Silver")

dbutils.notebook.exit(f"SUCCESS: {dedup_count} records processed, {final_record_count} total in Silver")


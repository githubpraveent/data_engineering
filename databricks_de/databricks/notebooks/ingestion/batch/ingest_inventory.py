"""
Databricks Notebook: Batch Ingestion - Inventory
Ingests inventory data from source systems into Bronze layer.
"""

# MAGIC %md
# MAGIC # Batch Ingestion: Inventory

# COMMAND ----------

# MAGIC %run ../../utilities/common_functions
# MAGIC %run ../../utilities/schema_definitions

# COMMAND ----------

# Configuration
dbutils.widgets.text("source_system", "inventory_db", "Source System")
dbutils.widgets.text("environment", "dev", "Environment")
dbutils.widgets.text("catalog", "retail_datalake", "Unity Catalog")
dbutils.widgets.text("bronze_schema", "bronze", "Bronze Schema Name")
dbutils.widgets.text("source_path", "", "Source Data Path")

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, current_timestamp
import logging

spark = SparkSession.builder.getOrCreate()
logger = setup_logging()

SOURCE_SYSTEM = dbutils.widgets.get("source_system")
ENVIRONMENT = dbutils.widgets.get("environment")
CATALOG = dbutils.widgets.get("catalog")
BRONZE_SCHEMA = dbutils.widgets.get("bronze_schema")
SOURCE_PATH = dbutils.widgets.get("source_path")

BRONZE_TABLE = f"{CATALOG}.{ENVIRONMENT}_{BRONZE_SCHEMA}.inventory"

logger.info(f"Starting batch ingestion for Inventory from {SOURCE_SYSTEM}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Read Source Data

# COMMAND ----------

# Read from source
# df_raw = spark.read.format("jdbc")...

# Sample data for demonstration
# Create a temporary schema without metadata fields (they'll be added later)
from pyspark.sql.types import StructType, StructField, StringType

temp_schema = StructType([
    StructField("product_id", StringType(), nullable=False),
    StructField("store_id", StringType(), nullable=True),
    StructField("quantity_on_hand", StringType(), nullable=True),
    StructField("quantity_reserved", StringType(), nullable=True),
    StructField("reorder_level", StringType(), nullable=True),
    StructField("last_updated", StringType(), nullable=True),
    StructField("unit_cost", StringType(), nullable=True),
])

df_raw = spark.createDataFrame([
    ("PROD001", "STORE001", "100", "10", "20", "2024-01-15 10:00:00", "25.50"),
    ("PROD002", "STORE001", "50", "5", "15", "2024-01-15 10:00:00", "15.75"),
], schema=temp_schema)

df_bronze = df_raw.withColumn("ingestion_timestamp", current_timestamp()) \
                  .withColumn("source_system", lit(SOURCE_SYSTEM)) \
                  .withColumn("raw_data", lit(None))

logger.info(f"Read {df_bronze.count()} records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write to Bronze

# COMMAND ----------

spark.sql(f"CREATE DATABASE IF NOT EXISTS {CATALOG}.{ENVIRONMENT}_{BRONZE_SCHEMA}")

df_bronze.write \
    .format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .saveAsTable(BRONZE_TABLE)

logger.info(f"Successfully wrote to {BRONZE_TABLE}")

# COMMAND ----------

try:
    spark.sql(f"ALTER TABLE {BRONZE_TABLE} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")
    logger.info("CDF enabled")
except Exception as e:
    logger.warning(f"Could not enable CDF: {e}")

# COMMAND ----------

record_count = df_bronze.count()
logger.info(f"Ingestion completed: {record_count} records")

dbutils.notebook.exit(f"SUCCESS: {record_count} records ingested into {BRONZE_TABLE}")


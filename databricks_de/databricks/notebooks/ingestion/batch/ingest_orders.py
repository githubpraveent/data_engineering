"""
Databricks Notebook: Batch Ingestion - Orders
Ingests orders data from source systems into Bronze layer (Delta Lake).
"""

# MAGIC %md
# MAGIC # Batch Ingestion: Orders
# MAGIC 
# MAGIC This notebook ingests orders data from source systems (e.g., PostgreSQL, MySQL, or CSV files)
# MAGIC into the Bronze layer of the Delta Lake.

# COMMAND ----------

# MAGIC %run ../utilities/common_functions
# MAGIC %run ../utilities/schema_definitions

# COMMAND ----------

# Configuration
dbutils.widgets.text("source_system", "orders_db", "Source System")
dbutils.widgets.text("environment", "dev", "Environment")
dbutils.widgets.text("catalog", "retail_datalake", "Unity Catalog")
dbutils.widgets.text("bronze_schema", "bronze", "Bronze Schema Name")
dbutils.widgets.text("source_path", "", "Source Data Path (S3/ADLS/GCS or JDBC connection string)")

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, current_timestamp, to_timestamp, to_date
import logging

# Initialize
spark = SparkSession.builder.getOrCreate()
logger = setup_logging()

# Get parameters
SOURCE_SYSTEM = dbutils.widgets.get("source_system")
ENVIRONMENT = dbutils.widgets.get("environment")
CATALOG = dbutils.widgets.get("catalog")
BRONZE_SCHEMA = dbutils.widgets.get("bronze_schema")
SOURCE_PATH = dbutils.widgets.get("source_path")

# Table paths
BRONZE_TABLE = f"{CATALOG}.{ENVIRONMENT}_{BRONZE_SCHEMA}.orders"

logger.info(f"Starting batch ingestion for Orders from {SOURCE_SYSTEM}")
logger.info(f"Target table: {BRONZE_TABLE}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Read Source Data

# COMMAND ----------

# Read from source (adjust based on your source system)
# Example 1: Read from JDBC (PostgreSQL, MySQL, etc.)
# df_raw = spark.read \
#     .format("jdbc") \
#     .option("url", SOURCE_PATH) \
#     .option("dbtable", "orders") \
#     .option("user", dbutils.secrets.get("retail-databricks", "db_user")) \
#     .option("password", dbutils.secrets.get("retail-databricks", "db_password")) \
#     .load()

# Example 2: Read from CSV/S3/ADLS/GCS
# df_raw = spark.read.format("csv") \
#     .option("header", "true") \
#     .option("inferSchema", "false") \
#     .load(SOURCE_PATH)

# Example 3: Read from Delta table (if source is already in Delta format)
# df_raw = spark.read.format("delta").table(SOURCE_PATH)

# For demonstration, creating sample data
# In production, replace this with actual source read logic
# Create a temporary schema without metadata fields (they'll be added later)
from pyspark.sql.types import StructType, StructField, StringType

temp_schema = StructType([
    StructField("order_id", StringType(), nullable=False),
    StructField("customer_id", StringType(), nullable=True),
    StructField("order_date", StringType(), nullable=True),
    StructField("order_status", StringType(), nullable=True),
    StructField("total_amount", StringType(), nullable=True),
    StructField("currency", StringType(), nullable=True),
    StructField("store_id", StringType(), nullable=True),
    StructField("payment_method", StringType(), nullable=True),
])

df_raw = spark.createDataFrame([
    ("ORD001", "CUST001", "2024-01-15", "COMPLETED", "150.00", "USD", "STORE001", "CREDIT_CARD"),
    ("ORD002", "CUST002", "2024-01-16", "PENDING", "75.50", "USD", "STORE002", "CASH"),
], schema=temp_schema)

# Add ingestion metadata
df_bronze = df_raw.withColumn("ingestion_timestamp", current_timestamp()) \
                  .withColumn("source_system", lit(SOURCE_SYSTEM)) \
                  .withColumn("raw_data", lit(None))  # In production, store full JSON payload if available

logger.info(f"Read {df_bronze.count()} records from source")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Validate Schema

# COMMAND ----------

# Validate that required columns exist
required_cols = ["order_id", "ingestion_timestamp", "source_system"]
missing_cols = [col for col in required_cols if col not in df_bronze.columns]

if missing_cols:
    raise ValueError(f"Missing required columns: {missing_cols}")

logger.info("Schema validation passed")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Write to Bronze Layer (Delta Table)

# COMMAND ----------

# Create database/schema if not exists
spark.sql(f"CREATE DATABASE IF NOT EXISTS {CATALOG}.{ENVIRONMENT}_{BRONZE_SCHEMA}")

# Write to Bronze Delta table
df_bronze.write \
    .format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .saveAsTable(BRONZE_TABLE)

logger.info(f"Successfully wrote data to {BRONZE_TABLE}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Enable Change Data Feed (CDF)

# COMMAND ----------

# Enable Change Data Feed for downstream CDC processing
try:
    spark.sql(f"ALTER TABLE {BRONZE_TABLE} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")
    logger.info("Change Data Feed enabled")
except Exception as e:
    logger.warning(f"Could not enable CDF: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Record Ingestion Metrics

# COMMAND ----------

# Record ingestion metrics
record_count = df_bronze.count()
ingestion_timestamp = current_timestamp()

metrics_df = spark.createDataFrame([(
    SOURCE_SYSTEM,
    "orders",
    BRONZE_TABLE,
    record_count,
    ingestion_timestamp,
    "SUCCESS"
)], schema="source_system string, table_name string, target_table string, record_count long, ingestion_timestamp timestamp, status string")

# Write metrics to monitoring table (if exists)
try:
    metrics_table = f"{CATALOG}.{ENVIRONMENT}_monitoring.ingestion_metrics"
    metrics_df.write.format("delta").mode("append").saveAsTable(metrics_table)
except:
    logger.info("Metrics table not available, skipping metrics write")

logger.info(f"Ingestion completed: {record_count} records ingested")

# COMMAND ----------

# Return success status
dbutils.notebook.exit(f"SUCCESS: {record_count} records ingested into {BRONZE_TABLE}")


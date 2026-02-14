"""
Databricks Notebook: Batch Ingestion - Customers
Ingests customers data from source systems into Bronze layer (Delta Lake).
"""

# MAGIC %md
# MAGIC # Batch Ingestion: Customers
# MAGIC 
# MAGIC This notebook ingests customers data from source systems into the Bronze layer.

# COMMAND ----------

# MAGIC %run ../../utilities/common_functions
# MAGIC %run ../../utilities/schema_definitions

# COMMAND ----------

# Configuration
dbutils.widgets.text("source_system", "customers_db", "Source System")
dbutils.widgets.text("environment", "dev", "Environment")
dbutils.widgets.text("catalog", "retail_datalake", "Unity Catalog")
dbutils.widgets.text("bronze_schema", "bronze", "Bronze Schema Name")
dbutils.widgets.text("source_path", "", "Source Data Path")

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, current_timestamp
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
BRONZE_TABLE = f"{CATALOG}.{ENVIRONMENT}_{BRONZE_SCHEMA}.customers"

logger.info(f"Starting batch ingestion for Customers from {SOURCE_SYSTEM}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Read Source Data

# COMMAND ----------

# Read from source (adjust based on your source system)
# Example: Read from JDBC
# df_raw = spark.read \
#     .format("jdbc") \
#     .option("url", SOURCE_PATH) \
#     .option("dbtable", "customers") \
#     .option("user", dbutils.secrets.get("retail-databricks", "db_user")) \
#     .option("password", dbutils.secrets.get("retail-databricks", "db_password")) \
#     .load()

# For demonstration, creating sample data
# Create a temporary schema without metadata fields (they'll be added later)
from pyspark.sql.types import StructType, StructField, StringType

temp_schema = StructType([
    StructField("customer_id", StringType(), nullable=False),
    StructField("first_name", StringType(), nullable=True),
    StructField("last_name", StringType(), nullable=True),
    StructField("email", StringType(), nullable=True),
    StructField("phone", StringType(), nullable=True),
    StructField("address", StringType(), nullable=True),
    StructField("city", StringType(), nullable=True),
    StructField("state", StringType(), nullable=True),
    StructField("zip_code", StringType(), nullable=True),
    StructField("country", StringType(), nullable=True),
    StructField("date_of_birth", StringType(), nullable=True),
    StructField("registration_date", StringType(), nullable=True),
])

df_raw = spark.createDataFrame([
    ("CUST001", "John", "Doe", "john.doe@email.com", "555-0101", "123 Main St", "New York", "NY", "10001", "USA", "1980-05-15", "2020-01-01"),
    ("CUST002", "Jane", "Smith", "jane.smith@email.com", "555-0102", "456 Oak Ave", "Los Angeles", "CA", "90001", "USA", "1985-08-20", "2020-02-15"),
], schema=temp_schema)

# Add ingestion metadata
df_bronze = df_raw.withColumn("ingestion_timestamp", current_timestamp()) \
                  .withColumn("source_system", lit(SOURCE_SYSTEM)) \
                  .withColumn("raw_data", lit(None))

logger.info(f"Read {df_bronze.count()} records from source")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Validate Schema

# COMMAND ----------

required_cols = ["customer_id", "ingestion_timestamp", "source_system"]
missing_cols = [col for col in required_cols if col not in df_bronze.columns]

if missing_cols:
    raise ValueError(f"Missing required columns: {missing_cols}")

logger.info("Schema validation passed")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Write to Bronze Layer

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
# MAGIC ## Step 4: Enable Change Data Feed

# COMMAND ----------

try:
    spark.sql(f"ALTER TABLE {BRONZE_TABLE} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")
    logger.info("Change Data Feed enabled")
except Exception as e:
    logger.warning(f"Could not enable CDF: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Record Metrics

# COMMAND ----------

record_count = df_bronze.count()
logger.info(f"Ingestion completed: {record_count} records ingested")

dbutils.notebook.exit(f"SUCCESS: {record_count} records ingested into {BRONZE_TABLE}")


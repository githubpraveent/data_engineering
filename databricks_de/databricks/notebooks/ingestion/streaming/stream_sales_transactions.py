"""
Databricks Notebook: Streaming Ingestion - Sales Transactions
Ingests real-time sales transaction events from Kafka into Bronze layer using Structured Streaming.
"""

# MAGIC %md
# MAGIC # Streaming Ingestion: Sales Transactions
# MAGIC 
# MAGIC This notebook uses Spark Structured Streaming to ingest real-time sales transactions
# MAGIC from Kafka (or other streaming sources) into the Bronze Delta Lake layer.

# COMMAND ----------

# MAGIC %run ../../utilities/common_functions
# MAGIC %run ../../utilities/schema_definitions

# COMMAND ----------

# Configuration
dbutils.widgets.text("kafka_bootstrap_servers", "", "Kafka Bootstrap Servers")
dbutils.widgets.text("kafka_topic", "sales_transactions", "Kafka Topic")
dbutils.widgets.text("starting_offsets", "latest", "Starting Offsets (earliest/latest)")
dbutils.widgets.text("environment", "dev", "Environment")
dbutils.widgets.text("catalog", "retail_datalake", "Unity Catalog")
dbutils.widgets.text("bronze_schema", "bronze", "Bronze Schema Name")
dbutils.widgets.text("checkpoint_location", "", "Checkpoint Location (S3/ADLS/GCS path)")

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, lit, current_timestamp, from_json, schema_of_json, 
    get_json_object, to_timestamp
)
from pyspark.sql.types import StringType
import logging

spark = SparkSession.builder.getOrCreate()
logger = setup_logging()

# Get parameters
KAFKA_BOOTSTRAP_SERVERS = dbutils.widgets.get("kafka_bootstrap_servers")
KAFKA_TOPIC = dbutils.widgets.get("kafka_topic")
STARTING_OFFSETS = dbutils.widgets.get("starting_offsets")
ENVIRONMENT = dbutils.widgets.get("environment")
CATALOG = dbutils.widgets.get("catalog")
BRONZE_SCHEMA = dbutils.widgets.get("bronze_schema")
CHECKPOINT_LOCATION = dbutils.widgets.get("checkpoint_location")

# Table paths
BRONZE_TABLE = f"{CATALOG}.{ENVIRONMENT}_{BRONZE_SCHEMA}.sales_transactions"

# Ensure checkpoint location is set
if not CHECKPOINT_LOCATION:
    CHECKPOINT_LOCATION = f"/tmp/checkpoints/{ENVIRONMENT}/sales_transactions"

logger.info(f"Starting streaming ingestion for Sales Transactions")
logger.info(f"Kafka topic: {KAFKA_TOPIC}, Target table: {BRONZE_TABLE}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Define Kafka Source

# COMMAND ----------

# Read from Kafka using Structured Streaming
df_kafka = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
    .option("subscribe", KAFKA_TOPIC) \
    .option("startingOffsets", STARTING_OFFSETS) \
    .option("failOnDataLoss", "false") \
    .load()

logger.info("Kafka source configured")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Parse JSON Payload

# COMMAND ----------

# Parse JSON payload from Kafka value
# Assuming Kafka messages are in JSON format
# Adjust schema based on your actual Kafka message structure

json_schema = """
{
  "transaction_id": "string",
  "store_id": "string",
  "product_id": "string",
  "customer_id": "string",
  "transaction_timestamp": "string",
  "quantity": "string",
  "unit_price": "string",
  "discount_amount": "string",
  "total_amount": "string",
  "payment_method": "string"
}
"""

df_parsed = df_kafka.select(
    get_json_object(col("value").cast("string"), "$.transaction_id").alias("transaction_id"),
    get_json_object(col("value").cast("string"), "$.store_id").alias("store_id"),
    get_json_object(col("value").cast("string"), "$.product_id").alias("product_id"),
    get_json_object(col("value").cast("string"), "$.customer_id").alias("customer_id"),
    to_timestamp(get_json_object(col("value").cast("string"), "$.transaction_timestamp")).alias("transaction_timestamp"),
    get_json_object(col("value").cast("string"), "$.quantity").alias("quantity"),
    get_json_object(col("value").cast("string"), "$.unit_price").alias("unit_price"),
    get_json_object(col("value").cast("string"), "$.discount_amount").alias("discount_amount"),
    get_json_object(col("value").cast("string"), "$.total_amount").alias("total_amount"),
    get_json_object(col("value").cast("string"), "$.payment_method").alias("payment_method"),
    col("value").cast("string").alias("raw_data"),
    col("timestamp").alias("kafka_timestamp"),
    col("partition"),
    col("offset")
)

logger.info("JSON parsing configured")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Add Metadata Columns

# COMMAND ----------

df_bronze = df_parsed.withColumn("ingestion_timestamp", current_timestamp()) \
                     .withColumn("source_system", lit("kafka_stream"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Create Bronze Table if Not Exists

# COMMAND ----------

# Create database/schema if not exists
spark.sql(f"CREATE DATABASE IF NOT EXISTS {CATALOG}.{ENVIRONMENT}_{BRONZE_SCHEMA}")

# Create Delta table if not exists (using batch write for initial creation)
try:
    # Try to read the table to see if it exists
    spark.table(BRONZE_TABLE).limit(1).collect()
    logger.info(f"Table {BRONZE_TABLE} already exists")
except:
    # Create empty table with schema
    empty_df = spark.createDataFrame([], schema=BRONZE_SALES_TRANSACTIONS_SCHEMA)
    empty_df.write.format("delta").saveAsTable(BRONZE_TABLE)
    logger.info(f"Created new table {BRONZE_TABLE}")

# Enable Change Data Feed
try:
    spark.sql(f"ALTER TABLE {BRONZE_TABLE} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")
    logger.info("Change Data Feed enabled")
except Exception as e:
    logger.warning(f"Could not enable CDF: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Write Stream to Delta Table

# COMMAND ----------

# Write stream to Delta table
query = df_bronze.writeStream \
    .format("delta") \
    .outputMode("append") \
    .option("checkpointLocation", CHECKPOINT_LOCATION) \
    .option("mergeSchema", "true") \
    .table(BRONZE_TABLE)

logger.info("Streaming query started")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6: Monitor Stream

# COMMAND ----------

# For production, this would typically run continuously
# For notebook execution, you can use:
# query.awaitTermination()

# Or use foreachBatch for more control:
def process_batch(batch_df, batch_id):
    """Process each micro-batch."""
    logger.info(f"Processing batch {batch_id}")
    batch_df.write \
        .format("delta") \
        .mode("append") \
        .option("mergeSchema", "true") \
        .saveAsTable(BRONZE_TABLE)

# Alternative streaming write with foreachBatch
# query = df_bronze.writeStream \
#     .foreachBatch(process_batch) \
#     .option("checkpointLocation", CHECKPOINT_LOCATION) \
#     .start()

# COMMAND ----------

logger.info("Streaming ingestion configured successfully")
dbutils.notebook.exit(f"SUCCESS: Streaming query configured for {BRONZE_TABLE}")


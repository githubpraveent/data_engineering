# Databricks notebook source
# MAGIC %md
# MAGIC # Stream POS Events from Event Hubs to ADLS Bronze
# MAGIC 
# MAGIC This notebook streams POS events from Azure Event Hubs and writes them to ADLS Gen2 Bronze layer in Delta format.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

# Get parameters from Airflow
dbutils.widgets.text("event_hub_name", "pos-events")
dbutils.widgets.text("consumer_group", "databricks-streaming")
dbutils.widgets.text("bronze_path", "")
dbutils.widgets.text("checkpoint_path", "")

event_hub_name = dbutils.widgets.get("event_hub_name")
consumer_group = dbutils.widgets.get("consumer_group")
bronze_path = dbutils.widgets.get("bronze_path")
checkpoint_path = dbutils.widgets.get("checkpoint_path")

# Event Hubs connection string (should be stored in Key Vault)
event_hubs_connection_string = dbutils.secrets.get(scope="azure-key-vault", key="event-hubs-connection-string")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Define Event Hubs Configuration

# COMMAND ----------

# Event Hubs configuration
ehConf = {
    'eventhubs.connectionString': event_hubs_connection_string,
    'eventhubs.consumerGroup': consumer_group,
    'eventhubs.startingPosition': 'latest'  # or 'earliest' for replay
}

# COMMAND ----------

# MAGIC %md
# MAGIC ## Stream from Event Hubs to Bronze

# COMMAND ----------

from pyspark.sql.types import *
from pyspark.sql.functions import *
from delta.tables import *

# Define schema for POS events
pos_event_schema = StructType([
    StructField("event_id", StringType(), True),
    StructField("store_id", StringType(), True),
    StructField("transaction_id", StringType(), True),
    StructField("customer_id", StringType(), True),
    StructField("product_id", StringType(), True),
    StructField("quantity", IntegerType(), True),
    StructField("price", DecimalType(10, 2), True),
    StructField("transaction_timestamp", TimestampType(), True),
    StructField("event_timestamp", TimestampType(), True)
])

# Read stream from Event Hubs
df_stream = (
    spark
    .readStream
    .format("eventhubs")
    .options(**ehConf)
    .load()
)

# Parse JSON body
df_parsed = df_stream.select(
    from_json(col("body").cast("string"), pos_event_schema).alias("data"),
    col("enqueuedTime").alias("enqueued_time"),
    col("partition").alias("partition_id"),
    col("offset").alias("offset_id")
).select("data.*", "enqueued_time", "partition_id", "offset_id")

# Add metadata columns
df_final = df_parsed.withColumn(
    "ingestion_timestamp", current_timestamp()
).withColumn(
    "processing_date", to_date(col("transaction_timestamp"))
)

# Write to Bronze layer in Delta format
query = (
    df_final
    .writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", checkpoint_path)
    .option("path", bronze_path)
    .partitionBy("processing_date", "store_id")
    .trigger(processingTime='10 seconds')
    .start()
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Monitor Streaming Query

# COMMAND ----------

# Wait for the streaming query to finish (for batch mode)
# For continuous streaming, this would run indefinitely
# query.awaitTermination()

# For testing, process for a specific duration
import time
time.sleep(60)  # Process for 60 seconds
query.stop()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Data in Bronze

# COMMAND ----------

# Read sample data from Bronze
df_bronze = spark.read.format("delta").load(bronze_path)
display(df_bronze.limit(100))

# Show statistics
print(f"Total records: {df_bronze.count()}")
df_bronze.groupBy("processing_date").count().orderBy("processing_date").show()


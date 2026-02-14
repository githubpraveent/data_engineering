# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze Layer: Real-Time Streaming Ingestion
# MAGIC 
# MAGIC This notebook implements the Bronze layer ingestion from Kafka/Event Hubs/Kinesis into Delta Lake.
# MAGIC 
# MAGIC **Features:**
# MAGIC - Schema enforcement
# MAGIC - Checkpointing for fault tolerance
# MAGIC - Exactly-once processing guarantees
# MAGIC - Support for multiple streaming sources

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

import json
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, current_timestamp, 
    lit, when, regexp_replace, split
)
from pyspark.sql.types import (
    StructType, StructField, StringType, 
    TimestampType, DoubleType, IntegerType, MapType
)

# Load configuration
config_path = "/Workspace/Shared/lakehouse/config/kafka_config.json"
with open(config_path, 'r') as f:
    config = json.load(f)

# Get workspace configuration
workspace_config = dbutils.widgets.get("workspace_config") or "/Workspace/Shared/lakehouse/config/workspace_config.json"
with open(workspace_config, 'r') as f:
    ws_config = json.load(f)

# Set up paths
catalog = ws_config["workspace"]["catalog"]
checkpoint_location = f"{ws_config['workspace']['checkpoint_root']}bronze/customer_events"
table_name = f"{catalog}.bronze.customer_events_raw"

# Kafka configuration
kafka_config = config["kafka"]
bootstrap_servers = kafka_config["bootstrap_servers"]
topic = kafka_config["topics"]["customer_events"]

# Get credentials from Databricks secrets
username = dbutils.secrets.get(
    scope=kafka_config["secrets"]["username_secret_scope"],
    key=kafka_config["secrets"]["username_secret_key"]
)
password = dbutils.secrets.get(
    scope=kafka_config["secrets"]["password_secret_scope"],
    key=kafka_config["secrets"]["password_secret_key"]
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Define Schema

# COMMAND ----------

# Expected schema for customer events
customer_event_schema = StructType([
    StructField("event_id", StringType(), False),
    StructField("customer_id", StringType(), False),
    StructField("event_type", StringType(), False),  # click, purchase, review, page_view
    StructField("timestamp", TimestampType(), False),
    StructField("session_id", StringType(), True),
    StructField("product_id", StringType(), True),
    StructField("amount", DoubleType(), True),
    StructField("currency", StringType(), True),
    StructField("text_content", StringType(), True),  # For reviews
    StructField("rating", IntegerType(), True),
    StructField("page_url", StringType(), True),
    StructField("user_agent", StringType(), True),
    StructField("ip_address", StringType(), True),
    StructField("metadata", MapType(StringType(), StringType()), True)
])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Streaming Ingestion from Kafka

# COMMAND ----------

def create_bronze_stream():
    """
    Create a streaming DataFrame from Kafka source.
    Supports Kafka, Event Hubs, and Kinesis.
    """
    
    # Read from Kafka
    df_raw = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", bootstrap_servers)
        .option("subscribe", topic)
        .option("kafka.security.protocol", kafka_config.get("security_protocol", "SASL_SSL"))
        .option("kafka.sasl.mechanism", kafka_config.get("sasl_mechanism", "PLAIN"))
        .option("kafka.sasl.jaas.config", 
                f'org.apache.kafka.common.security.plain.PlainLoginModule required username="{username}" password="{password}";')
        .option("kafka.group.id", kafka_config["consumer"]["group_id"])
        .option("startingOffsets", kafka_config["consumer"]["auto_offset_reset"])
        .option("failOnDataLoss", "false")
        .option("maxOffsetsPerTrigger", 10000)  # Control batch size
        .load()
    )
    
    return df_raw

# COMMAND ----------

# MAGIC %md
# MAGIC ## Parse and Transform Raw Data

# COMMAND ----------

def parse_kafka_messages(df_raw):
    """
    Parse Kafka messages and extract structured data.
    """
    
    # Parse JSON from Kafka value
    df_parsed = (
        df_raw
        .select(
            col("key").cast("string").alias("kafka_key"),
            col("value").cast("string").alias("raw_value"),
            col("timestamp").alias("kafka_timestamp"),
            col("partition"),
            col("offset")
        )
        .withColumn(
            "parsed_data",
            from_json(col("raw_value"), customer_event_schema)
        )
        .select(
            col("kafka_key"),
            col("kafka_timestamp"),
            col("partition"),
            col("offset"),
            col("parsed_data.*")
        )
        .withColumn("ingestion_timestamp", current_timestamp())
        .withColumn("source", lit("kafka"))
        .withColumn("topic", lit(topic))
    )
    
    return df_parsed

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Quality Checks

# COMMAND ----------

def apply_bronze_quality_checks(df):
    """
    Apply basic data quality checks at Bronze layer.
    """
    
    df_quality = (
        df
        .withColumn(
            "is_valid",
            when(
                (col("event_id").isNotNull()) &
                (col("customer_id").isNotNull()) &
                (col("event_type").isNotNull()) &
                (col("timestamp").isNotNull()),
                lit(True)
            ).otherwise(lit(False))
        )
        .withColumn(
            "quality_score",
            when(col("is_valid"), lit(1.0))
            .otherwise(lit(0.0))
        )
        .withColumn(
            "error_message",
            when(
                col("event_id").isNull(), lit("Missing event_id")
            )
            .when(
                col("customer_id").isNull(), lit("Missing customer_id")
            )
            .when(
                col("event_type").isNull(), lit("Missing event_type")
            )
            .when(
                col("timestamp").isNull(), lit("Missing timestamp")
            )
            .otherwise(lit(None))
        )
    )
    
    return df_quality

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write to Delta Lake (Bronze Table)

# COMMAND ----------

def write_to_bronze(df, table_name, checkpoint_location):
    """
    Write streaming data to Delta Lake Bronze table.
    """
    
    query = (
        df.writeStream
        .format("delta")
        .outputMode("append")
        .option("checkpointLocation", checkpoint_location)
        .option("mergeSchema", "true")  # Allow schema evolution
        .option("maxFilesPerTrigger", 100)  # Control file size
        .table(table_name)
    )
    
    return query

# COMMAND ----------

# MAGIC %md
# MAGIC ## Main Streaming Pipeline

# COMMAND ----------

# Create streaming source
df_raw = create_bronze_stream()

# Parse messages
df_parsed = parse_kafka_messages(df_raw)

# Apply quality checks
df_bronze = apply_bronze_quality_checks(df_parsed)

# Write to Delta table
streaming_query = write_to_bronze(df_bronze, table_name, checkpoint_location)

# Start the stream
print(f"Starting streaming ingestion to {table_name}")
print(f"Checkpoint location: {checkpoint_location}")

# For interactive mode, use awaitTermination()
# For production, deploy as a job and it will run continuously
# streaming_query.awaitTermination()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Alternative: Event Hubs Source

# COMMAND ----------

def create_event_hubs_stream():
    """
    Alternative implementation for Azure Event Hubs.
    """
    connection_string = dbutils.secrets.get(
        scope=config["event_hubs"]["connection_string_secret_scope"],
        key=config["event_hubs"]["connection_string_secret_key"]
    )
    event_hub_name = config["event_hubs"]["event_hub_name"]
    consumer_group = config["event_hubs"]["consumer_group"]
    
    df_raw = (
        spark.readStream
        .format("eventhubs")
        .option("eventhubs.connectionString", connection_string)
        .option("eventhubs.consumerGroup", consumer_group)
        .option("eventhubs.startingPosition", "latest")
        .load()
    )
    
    return df_raw

# COMMAND ----------

# MAGIC %md
# MAGIC ## Alternative: Kinesis Source

# COMMAND ----------

def create_kinesis_stream():
    """
    Alternative implementation for AWS Kinesis.
    """
    kinesis_config = config["kinesis"]
    stream_name = kinesis_config["stream_name"]
    region = kinesis_config["region"]
    
    aws_access_key = dbutils.secrets.get(
        scope=kinesis_config["aws_access_key_secret_scope"],
        key=kinesis_config["aws_access_key_secret_key"]
    )
    aws_secret_key = dbutils.secrets.get(
        scope=kinesis_config["aws_secret_key_secret_scope"],
        key=kinesis_config["aws_secret_key_secret_key"]
    )
    
    df_raw = (
        spark.readStream
        .format("kinesis")
        .option("streamName", stream_name)
        .option("region", region)
        .option("awsAccessKeyId", aws_access_key)
        .option("awsSecretKey", aws_secret_key)
        .option("startingPosition", "LATEST")
        .load()
    )
    
    return df_raw

# COMMAND ----------

# MAGIC %md
# MAGIC ## Monitoring: Check Stream Status

# COMMAND ----------

def get_stream_metrics(query):
    """
    Get streaming metrics for monitoring.
    """
    if query.isActive:
        progress = query.lastProgress
        return {
            "is_active": True,
            "batch_id": progress.get("batchId"),
            "input_rows_per_second": progress.get("inputRowsPerSecond", 0),
            "processed_rows_per_second": progress.get("processedRowsPerSecond", 0),
            "num_input_rows": progress.get("numInputRows", 0),
            "timestamp": progress.get("timestamp")
        }
    else:
        return {"is_active": False}

# Example usage:
# metrics = get_stream_metrics(streaming_query)
# print(json.dumps(metrics, indent=2))

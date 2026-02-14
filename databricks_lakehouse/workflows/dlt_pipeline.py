# Databricks notebook source
# Delta Live Tables Pipeline
# This notebook defines a complete DLT pipeline for the medallion architecture

import dlt
from pyspark.sql.functions import *
from pyspark.sql.types import *

# Configuration
catalog = "lakehouse"
kafka_bootstrap_servers = dbutils.secrets.get(scope="kafka", key="bootstrap_servers")
kafka_topic = "customer-behavior-events"
kafka_username = dbutils.secrets.get(scope="kafka", key="username")
kafka_password = dbutils.secrets.get(scope="kafka", key="password")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bronze Layer: Raw Ingestion

# COMMAND ----------

@dlt.table(
    name="customer_events_raw",
    comment="Bronze layer: Raw customer events from Kafka",
    table_properties={
        "quality": "bronze",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true"
    }
)
def bronze_customer_events():
    """
    Stream raw events from Kafka into Bronze Delta table.
    """
    return (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", kafka_bootstrap_servers)
        .option("subscribe", kafka_topic)
        .option("kafka.security.protocol", "SASL_SSL")
        .option("kafka.sasl.mechanism", "PLAIN")
        .option("kafka.sasl.jaas.config", 
                f'org.apache.kafka.common.security.plain.PlainLoginModule required username="{kafka_username}" password="{kafka_password}";')
        .option("startingOffsets", "latest")
        .load()
        .select(
            col("key").cast("string").alias("kafka_key"),
            col("value").cast("string").alias("raw_value"),
            col("timestamp").alias("kafka_timestamp"),
            col("partition"),
            col("offset")
        )
        .withColumn("ingestion_timestamp", current_timestamp())
        .withColumn("source", lit("kafka"))
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver Layer: Cleaned & Enriched

# COMMAND ----------

# Define schema for parsing
customer_event_schema = StructType([
    StructField("event_id", StringType(), False),
    StructField("customer_id", StringType(), False),
    StructField("event_type", StringType(), False),
    StructField("timestamp", TimestampType(), False),
    StructField("session_id", StringType(), True),
    StructField("product_id", StringType(), True),
    StructField("amount", DoubleType(), True),
    StructField("currency", StringType(), True),
    StructField("text_content", StringType(), True),
    StructField("rating", IntegerType(), True)
])

@dlt.table(
    name="customer_events_cleaned",
    comment="Silver layer: Cleaned and enriched customer events",
    table_properties={
        "quality": "silver",
        "delta.autoOptimize.optimizeWrite": "true"
    }
)
@dlt.expect_or_drop("valid_event_id", "event_id IS NOT NULL")
@dlt.expect_or_drop("valid_customer_id", "customer_id IS NOT NULL")
@dlt.expect_or_drop("valid_timestamp", "timestamp IS NOT NULL")
@dlt.expect("valid_amount_range", "amount IS NULL OR (amount >= 0 AND amount <= 1000000)")
@dlt.expect("valid_rating_range", "rating IS NULL OR (rating >= 0 AND rating <= 5)")
def silver_customer_events():
    """
    Transform Bronze data to Silver: parse JSON, clean, validate, enrich.
    """
    df_bronze = dlt.read_stream("customer_events_raw")
    
    # Parse JSON
    df_parsed = (
        df_bronze
        .withColumn(
            "parsed_data",
            from_json(col("raw_value"), customer_event_schema)
        )
        .select(
            col("parsed_data.*"),
            col("ingestion_timestamp"),
            col("source")
        )
    )
    
    # Clean and transform
    df_cleaned = (
        df_parsed
        .withColumn("event_type", upper(trim(col("event_type"))))
        .withColumn("currency", upper(coalesce(col("currency"), lit("USD"))))
        .withColumn("text_content", trim(col("text_content")))
        .withColumn("event_date", to_date(col("timestamp")))
        .withColumn("is_purchase", col("event_type") == "PURCHASE")
        .withColumn("is_review", col("event_type") == "REVIEW")
        .withColumn("processing_timestamp", current_timestamp())
    )
    
    return df_cleaned

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold Layer: Aggregations

# COMMAND ----------

@dlt.table(
    name="customer_behavior_daily",
    comment="Gold layer: Daily customer behavior aggregations",
    table_properties={
        "quality": "gold"
    },
    partition_cols=["event_date"]
)
def gold_customer_behavior_daily():
    """
    Aggregate customer behavior by day.
    """
    df_silver = dlt.read("customer_events_cleaned")
    
    return (
        df_silver
        .groupBy("customer_id", "event_date")
        .agg(
            count("*").alias("total_events"),
            countDistinct("session_id").alias("unique_sessions"),
            sum(when(col("is_purchase"), 1).otherwise(0)).alias("total_purchases"),
            sum(col("amount")).alias("total_revenue"),
            avg(col("amount")).alias("avg_transaction_value"),
            max(col("amount")).alias("max_transaction_value"),
            countDistinct("product_id").alias("unique_products_viewed")
        )
        .withColumn("conversion_rate",
                   when(col("total_events") > 0,
                       col("total_purchases") / col("total_events"))
                   .otherwise(lit(0.0)))
        .withColumn("processing_timestamp", current_timestamp())
    )

# COMMAND ----------

@dlt.table(
    name="sentiment_summary",
    comment="Gold layer: Sentiment summary by time period",
    partition_cols=["date"]
)
def gold_sentiment_summary():
    """
    Aggregate sentiment scores from reviews.
    """
    df_silver = dlt.read("customer_events_cleaned")
    
    return (
        df_silver
        .filter(
            (col("is_review") == True) &
            (col("text_content") != "") &
            (col("sentiment_score").isNotNull())
        )
        .groupBy(
            to_date(col("timestamp")).alias("date"),
            "category"
        )
        .agg(
            count("*").alias("total_reviews"),
            avg("sentiment_score").alias("avg_sentiment_score"),
            avg("rating").alias("avg_rating"),
            sum(when(col("sentiment_score") > 0.6, 1).otherwise(0)).alias("positive_reviews"),
            sum(when(col("sentiment_score") < 0.4, 1).otherwise(0)).alias("negative_reviews")
        )
        .withColumn("positive_sentiment_ratio",
                   col("positive_reviews") / col("total_reviews"))
        .withColumn("processing_timestamp", current_timestamp())
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Quality Metrics

# COMMAND ----------

@dlt.table(
    name="data_quality_metrics",
    comment="Data quality metrics for monitoring"
)
def data_quality_metrics():
    """
    Calculate data quality metrics.
    """
    df_silver = dlt.read("customer_events_cleaned")
    
    return (
        df_silver
        .groupBy("event_date")
        .agg(
            count("*").alias("total_records"),
            count(when(col("event_id").isNull(), 1)).alias("null_event_ids"),
            count(when(col("customer_id").isNull(), 1)).alias("null_customer_ids"),
            count(when(col("amount") < 0, 1)).alias("negative_amounts"),
            count(when(col("rating") < 0 | col("rating") > 5, 1)).alias("invalid_ratings")
        )
        .withColumn("quality_score",
                   (col("total_records") - 
                    col("null_event_ids") - 
                    col("null_customer_ids") - 
                    col("negative_amounts") - 
                    col("invalid_ratings")) / col("total_records"))
        .withColumn("processing_timestamp", current_timestamp())
    )

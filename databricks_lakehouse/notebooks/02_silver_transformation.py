# Databricks notebook source
# MAGIC %md
# MAGIC # Silver Layer: Data Cleaning & Enrichment
# MAGIC 
# MAGIC This notebook transforms Bronze raw data into cleaned, validated, and enriched Silver layer.
# MAGIC 
# MAGIC **Transformations:**
# MAGIC - Schema validation and type conversion
# MAGIC - Deduplication based on event_id
# MAGIC - Data quality checks and validation
# MAGIC - Enrichment with customer and product data
# MAGIC - Null handling and data normalization

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

import json
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, when, coalesce, trim, upper, lower,
    regexp_replace, split, to_date, to_timestamp,
    current_timestamp, lit, md5, sha2,
    window, count, sum as spark_sum, avg, max as spark_max,
    row_number, hour, dayofweek, datediff
)
from pyspark.sql.window import Window
from delta.tables import DeltaTable

# Load configuration
workspace_config_path = "/Workspace/Shared/lakehouse/config/workspace_config.json"
with open(workspace_config_path, 'r') as f:
    ws_config = json.load(f)

catalog = ws_config["workspace"]["catalog"]
bronze_table = f"{catalog}.bronze.customer_events_raw"
silver_table = f"{catalog}.silver.customer_events_cleaned"
checkpoint_location = f"{ws_config['workspace']['checkpoint_root']}silver/customer_events"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Read from Bronze (Streaming)

# COMMAND ----------

def read_bronze_stream():
    """
    Read streaming data from Bronze table.
    """
    df_bronze = (
        spark.readStream
        .table(bronze_table)
        .filter(col("is_valid") == True)  # Only process valid records
    )
    
    return df_bronze

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Cleaning Functions

# COMMAND ----------

def clean_text_columns(df):
    """
    Clean and normalize text columns.
    """
    df_cleaned = (
        df
        .withColumn("event_type", upper(trim(col("event_type"))))
        .withColumn("currency", upper(trim(coalesce(col("currency"), lit("USD")))))
        .withColumn("text_content", trim(col("text_content")))
        .withColumn("page_url", trim(col("page_url")))
        .withColumn("user_agent", trim(col("user_agent")))
    )
    
    return df_cleaned

# COMMAND ----------

def validate_event_types(df):
    """
    Validate and standardize event types.
    """
    valid_event_types = ["CLICK", "PURCHASE", "REVIEW", "PAGE_VIEW", "CART_ADD", "CART_REMOVE"]
    
    df_validated = (
        df
        .withColumn(
            "event_type",
            when(col("event_type").isin(valid_event_types), col("event_type"))
            .otherwise(lit("UNKNOWN"))
        )
        .withColumn(
            "is_valid_event_type",
            col("event_type") != "UNKNOWN"
        )
    )
    
    return df_validated

# COMMAND ----------

def handle_nulls_and_defaults(df):
    """
    Handle null values with appropriate defaults.
    """
    df_filled = (
        df
        .withColumn("session_id", coalesce(col("session_id"), lit("UNKNOWN")))
        .withColumn("amount", coalesce(col("amount"), lit(0.0)))
        .withColumn("currency", coalesce(col("currency"), lit("USD")))
        .withColumn("rating", coalesce(col("rating"), lit(0)))
        .withColumn("text_content", coalesce(col("text_content"), lit("")))
    )
    
    return df_filled

# COMMAND ----------

def validate_data_ranges(df):
    """
    Validate data ranges and business rules.
    """
    df_validated = (
        df
        .withColumn(
            "amount_valid",
            (col("amount") >= 0) & (col("amount") <= 1000000)
        )
        .withColumn(
            "rating_valid",
            (col("rating") >= 0) & (col("rating") <= 5)
        )
        .withColumn(
            "timestamp_valid",
            col("timestamp") <= current_timestamp()
        )
        .withColumn(
            "is_data_valid",
            col("amount_valid") & col("rating_valid") & col("timestamp_valid")
        )
    )
    
    return df_validated

# COMMAND ----------

# MAGIC %md
# MAGIC ## Deduplication

# COMMAND ----------

def deduplicate_events(df):
    """
    Remove duplicate events based on event_id.
    Uses window function to keep the latest record.
    """
    window_spec = Window.partitionBy("event_id").orderBy(col("ingestion_timestamp").desc())
    
    df_deduped = (
        df
        .withColumn("row_number", row_number().over(window_spec))
        .filter(col("row_number") == 1)
        .drop("row_number")
    )
    
    return df_deduped

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Enrichment

# COMMAND ----------

def enrich_with_customer_data(df):
    """
    Enrich events with customer demographic data.
    Assumes customer lookup table exists in Gold layer.
    """
    try:
        # Read customer dimension table (if exists)
        customer_dim = spark.table(f"{catalog}.gold.customer_dimension")
        
        df_enriched = (
            df
            .join(
                customer_dim.select(
                    "customer_id",
                    "customer_segment",
                    "registration_date",
                    "country",
                    "age_group"
                ),
                on="customer_id",
                how="left"
            )
        )
    except:
        # If dimension table doesn't exist, add null columns
        df_enriched = (
            df
            .withColumn("customer_segment", lit(None).cast("string"))
            .withColumn("registration_date", lit(None).cast("date"))
            .withColumn("country", lit(None).cast("string"))
            .withColumn("age_group", lit(None).cast("string"))
        )
    
    return df_enriched

# COMMAND ----------

def enrich_with_product_data(df):
    """
    Enrich events with product information.
    """
    try:
        product_dim = spark.table(f"{catalog}.gold.product_dimension")
        
        df_enriched = (
            df
            .join(
                product_dim.select(
                    "product_id",
                    "product_name",
                    "category",
                    "subcategory",
                    "brand",
                    "price"
                ),
                on="product_id",
                how="left"
            )
        )
    except:
        df_enriched = (
            df
            .withColumn("product_name", lit(None).cast("string"))
            .withColumn("category", lit(None).cast("string"))
            .withColumn("subcategory", lit(None).cast("string"))
            .withColumn("brand", lit(None).cast("string"))
            .withColumn("price", lit(None).cast("double"))
        )
    
    return df_enriched

# COMMAND ----------

def add_derived_columns(df):
    """
    Add derived columns for analytics.
    """
    df_derived = (
        df
        .withColumn("event_date", to_date(col("timestamp")))
        .withColumn("event_hour", hour(col("timestamp")))
        .withColumn("event_day_of_week", dayofweek(col("timestamp")))
        .withColumn("is_weekend", 
                   when(dayofweek(col("timestamp")).isin([1, 7]), lit(True))
                   .otherwise(lit(False)))
        .withColumn("is_purchase", col("event_type") == "PURCHASE")
        .withColumn("is_review", col("event_type") == "REVIEW")
        .withColumn("has_text_content", col("text_content") != "")
        .withColumn("processing_timestamp", current_timestamp())
    )
    
    return df_derived

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Quality Scoring

# COMMAND ----------

def calculate_quality_score(df):
    """
    Calculate comprehensive data quality score.
    """
    df_scored = (
        df
        .withColumn(
            "quality_score",
            (
                when(col("is_valid_event_type"), lit(0.2)).otherwise(lit(0.0)) +
                when(col("is_data_valid"), lit(0.2)).otherwise(lit(0.0)) +
                when(col("customer_id").isNotNull(), lit(0.2)).otherwise(lit(0.0)) +
                when(col("product_id").isNotNull(), lit(0.2)).otherwise(lit(0.0)) +
                when(col("timestamp").isNotNull(), lit(0.2)).otherwise(lit(0.0))
            )
        )
        .withColumn(
            "is_high_quality",
            col("quality_score") >= 0.8
        )
    )
    
    return df_scored

# COMMAND ----------

# MAGIC %md
# MAGIC ## Main Transformation Pipeline

# COMMAND ----------

def transform_bronze_to_silver(df_bronze):
    """
    Complete transformation pipeline from Bronze to Silver.
    """
    # Clean text columns
    df = clean_text_columns(df_bronze)
    
    # Validate event types
    df = validate_event_types(df)
    
    # Handle nulls
    df = handle_nulls_and_defaults(df)
    
    # Validate ranges
    df = validate_data_ranges(df)
    
    # Deduplicate
    df = deduplicate_events(df)
    
    # Enrich with customer data
    df = enrich_with_customer_data(df)
    
    # Enrich with product data
    df = enrich_with_product_data(df)
    
    # Add derived columns
    df = add_derived_columns(df)
    
    # Calculate quality score
    df = calculate_quality_score(df)
    
    return df

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write to Silver Table

# COMMAND ----------

def write_to_silver(df_silver, table_name, checkpoint_location):
    """
    Write transformed data to Silver Delta table.
    Uses merge for deduplication at write time.
    """
    
    # For streaming, use merge for upsert logic
    def upsert_to_silver(microBatchDF, batchId):
        """
        Upsert function for streaming writes.
        """
        # Create DeltaTable reference
        silver_delta = DeltaTable.forName(spark, table_name)
        
        # Merge logic: update if exists, insert if new
        merge_condition = "target.event_id = source.event_id"
        
        update_dict = {
            "customer_id": "source.customer_id",
            "event_type": "source.event_type",
            "timestamp": "source.timestamp",
            "amount": "source.amount",
            "currency": "source.currency",
            "text_content": "source.text_content",
            "rating": "source.rating",
            "quality_score": "source.quality_score",
            "processing_timestamp": "source.processing_timestamp"
        }
        
        (
            silver_delta.alias("target")
            .merge(
                microBatchDF.alias("source"),
                merge_condition
            )
            .whenMatchedUpdate(set=update_dict)
            .whenNotMatchedInsertAll()
            .execute()
        )
    
    # Write stream with merge
    query = (
        df_silver.writeStream
        .foreachBatch(upsert_to_silver)
        .outputMode("update")
        .option("checkpointLocation", checkpoint_location)
        .trigger(processingTime='10 seconds')  # Process every 10 seconds
        .start()
    )
    
    return query

# COMMAND ----------

# MAGIC %md
# MAGIC ## Execute Pipeline

# COMMAND ----------

# Read from Bronze
df_bronze = read_bronze_stream()

# Transform to Silver
df_silver = transform_bronze_to_silver(df_bronze)

# Write to Silver table
streaming_query = write_to_silver(df_silver, silver_table, checkpoint_location)

print(f"Silver transformation pipeline started")
print(f"Writing to: {silver_table}")
print(f"Checkpoint: {checkpoint_location}")

# For production, this runs continuously
# streaming_query.awaitTermination()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Quality Monitoring

# COMMAND ----------

def get_silver_quality_metrics():
    """
    Calculate data quality metrics for monitoring.
    """
    df_silver = spark.table(silver_table)
    
    metrics = (
        df_silver
        .agg(
            count("*").alias("total_records"),
            avg("quality_score").alias("avg_quality_score"),
            spark_sum(when(col("is_high_quality"), 1).otherwise(0)).alias("high_quality_count"),
            spark_sum(when(col("is_valid_event_type") == False, 1).otherwise(0)).alias("invalid_event_types"),
            spark_sum(when(col("is_data_valid") == False, 1).otherwise(0)).alias("invalid_data_records")
        )
    )
    
    return metrics

# Display metrics
quality_metrics = get_silver_quality_metrics()
display(quality_metrics)

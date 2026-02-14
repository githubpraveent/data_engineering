# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Layer: Analytics-Ready Aggregations
# MAGIC 
# MAGIC This notebook creates aggregated, analytics-ready datasets in the Gold layer.
# MAGIC 
# MAGIC **Outputs:**
# MAGIC - Daily customer behavior aggregations
# MAGIC - Sentiment summary by time period
# MAGIC - Customer feature sets for ML
# MAGIC - Product performance metrics

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

import json
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, sum as spark_sum, avg, count, countDistinct,
    max as spark_max, min as spark_min, collect_list,
    window, to_date, date_format, when, lit,
    first, last, percentile_approx, stddev,
    current_date, current_timestamp, datediff
)
from pyspark.sql.window import Window
from delta.tables import DeltaTable

# Load configuration
workspace_config_path = "/Workspace/Shared/lakehouse/config/workspace_config.json"
with open(workspace_config_path, 'r') as f:
    ws_config = json.load(f)

catalog = ws_config["workspace"]["catalog"]
silver_table = f"{catalog}.silver.customer_events_cleaned"

# Gold table names
gold_customer_behavior = f"{catalog}.gold.customer_behavior_daily"
gold_sentiment_summary = f"{catalog}.gold.sentiment_summary"
gold_customer_features = f"{catalog}.gold.customer_features"
gold_product_performance = f"{catalog}.gold.product_performance"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Read from Silver

# COMMAND ----------

def read_silver_data():
    """
    Read cleaned data from Silver layer.
    """
    df_silver = spark.table(silver_table)
    return df_silver

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold Table 1: Daily Customer Behavior

# COMMAND ----------

def create_customer_behavior_daily(df_silver):
    """
    Create daily aggregations of customer behavior.
    """
    df_behavior = (
        df_silver
        .filter(col("is_high_quality") == True)  # Only high-quality records
        .groupBy("customer_id", "event_date")
        .agg(
            count("*").alias("total_events"),
            countDistinct("session_id").alias("unique_sessions"),
            spark_sum(when(col("is_purchase"), 1).otherwise(0)).alias("total_purchases"),
            spark_sum(col("amount")).alias("total_revenue"),
            avg(col("amount")).alias("avg_transaction_value"),
            spark_max(col("amount")).alias("max_transaction_value"),
            countDistinct("product_id").alias("unique_products_viewed"),
            spark_sum(when(col("event_type") == "CLICK", 1).otherwise(0)).alias("total_clicks"),
            spark_sum(when(col("event_type") == "PAGE_VIEW", 1).otherwise(0)).alias("total_page_views"),
            spark_sum(when(col("event_type") == "REVIEW", 1).otherwise(0)).alias("total_reviews"),
            avg(when(col("is_review"), col("rating")).otherwise(None)).alias("avg_rating_given"),
            first("customer_segment").alias("customer_segment"),
            first("country").alias("country"),
            first("age_group").alias("age_group")
        )
        .withColumn("revenue_per_session", 
                   when(col("unique_sessions") > 0, 
                       col("total_revenue") / col("unique_sessions"))
                   .otherwise(lit(0.0)))
        .withColumn("conversion_rate",
                   when(col("total_events") > 0,
                       col("total_purchases") / col("total_events"))
                   .otherwise(lit(0.0)))
        .withColumn("processing_date", current_timestamp())
    )
    
    return df_behavior

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold Table 2: Sentiment Summary

# COMMAND ----------

def create_sentiment_summary(df_silver):
    """
    Create sentiment summary aggregations.
    Note: Assumes sentiment scores are added during ML inference.
    """
    df_sentiment = (
        df_silver
        .filter(
            (col("is_review") == True) &
            (col("text_content") != "") &
            (col("sentiment_score").isNotNull())  # From ML inference
        )
        .groupBy(
            to_date(col("timestamp")).alias("date"),
            "category",
            "customer_segment"
        )
        .agg(
            count("*").alias("total_reviews"),
            avg("sentiment_score").alias("avg_sentiment_score"),
            avg("rating").alias("avg_rating"),
            percentile_approx("sentiment_score", 0.5).alias("median_sentiment_score"),
            stddev("sentiment_score").alias("sentiment_stddev"),
            spark_sum(when(col("sentiment_score") > 0.6, 1).otherwise(0)).alias("positive_reviews"),
            spark_sum(when(col("sentiment_score") < 0.4, 1).otherwise(0)).alias("negative_reviews"),
            spark_sum(when(
                (col("sentiment_score") >= 0.4) & (col("sentiment_score") <= 0.6),
                1
            ).otherwise(0)).alias("neutral_reviews")
        )
        .withColumn("positive_sentiment_ratio",
                   col("positive_reviews") / col("total_reviews"))
        .withColumn("negative_sentiment_ratio",
                   col("negative_reviews") / col("total_reviews"))
        .withColumn("processing_timestamp", current_timestamp())
    )
    
    return df_sentiment

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold Table 3: Customer Features (ML-Ready)

# COMMAND ----------

def create_customer_features(df_silver):
    """
    Create ML-ready feature set for customers.
    Includes rolling window aggregations.
    """
    
    # First, get daily aggregations
    df_daily = create_customer_behavior_daily(df_silver)
    
    # Define window for rolling features (last 7, 30, 90 days)
    window_7d = Window.partitionBy("customer_id").orderBy("event_date").rowsBetween(-6, 0)
    window_30d = Window.partitionBy("customer_id").orderBy("event_date").rowsBetween(-29, 0)
    window_90d = Window.partitionBy("customer_id").orderBy("event_date").rowsBetween(-89, 0)
    
    df_features = (
        df_daily
        .withColumn("revenue_7d", spark_sum("total_revenue").over(window_7d))
        .withColumn("revenue_30d", spark_sum("total_revenue").over(window_30d))
        .withColumn("revenue_90d", spark_sum("total_revenue").over(window_90d))
        .withColumn("purchases_7d", spark_sum("total_purchases").over(window_7d))
        .withColumn("purchases_30d", spark_sum("total_purchases").over(window_30d))
        .withColumn("purchases_90d", spark_sum("total_purchases").over(window_90d))
        .withColumn("events_7d", spark_sum("total_events").over(window_7d))
        .withColumn("events_30d", spark_sum("total_events").over(window_30d))
        .withColumn("events_90d", spark_sum("total_events").over(window_90d))
        .withColumn("avg_revenue_7d", avg("total_revenue").over(window_7d))
        .withColumn("avg_revenue_30d", avg("total_revenue").over(window_30d))
        .withColumn("conversion_rate_7d",
                   when(spark_sum("total_events").over(window_7d) > 0,
                       spark_sum("total_purchases").over(window_7d) / 
                       spark_sum("total_events").over(window_7d))
                   .otherwise(lit(0.0)))
        .withColumn("conversion_rate_30d",
                   when(spark_sum("total_events").over(window_30d) > 0,
                       spark_sum("total_purchases").over(window_30d) / 
                       spark_sum("total_events").over(window_30d))
                   .otherwise(lit(0.0)))
        .withColumn("days_since_last_purchase",
                   datediff(current_date(), 
                           spark_max("event_date").over(
                               Window.partitionBy("customer_id")
                           )))
        .withColumn("customer_lifetime_value",
                   spark_sum("total_revenue").over(
                       Window.partitionBy("customer_id")
                   ))
        .withColumn("total_lifetime_purchases",
                   spark_sum("total_purchases").over(
                       Window.partitionBy("customer_id")
                   ))
        .select(
            "customer_id",
            "event_date",
            "customer_segment",
            "country",
            "age_group",
            "revenue_7d", "revenue_30d", "revenue_90d",
            "purchases_7d", "purchases_30d", "purchases_90d",
            "events_7d", "events_30d", "events_90d",
            "avg_revenue_7d", "avg_revenue_30d",
            "conversion_rate_7d", "conversion_rate_30d",
            "days_since_last_purchase",
            "customer_lifetime_value",
            "total_lifetime_purchases",
            "processing_timestamp"
        )
    )
    
    return df_features

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold Table 4: Product Performance

# COMMAND ----------

def create_product_performance(df_silver):
    """
    Create product performance aggregations.
    """
    df_product = (
        df_silver
        .filter(
            (col("product_id").isNotNull()) &
            (col("is_high_quality") == True)
        )
        .groupBy(
            "product_id",
            "product_name",
            "category",
            "subcategory",
            "brand",
            to_date(col("timestamp")).alias("date")
        )
        .agg(
            count("*").alias("total_views"),
            countDistinct("customer_id").alias("unique_customers"),
            spark_sum(when(col("is_purchase"), 1).otherwise(0)).alias("total_purchases"),
            spark_sum(when(col("is_purchase"), col("amount")).otherwise(0)).alias("total_revenue"),
            avg(when(col("is_purchase"), col("amount")).otherwise(None)).alias("avg_sale_price"),
            spark_sum(when(col("is_review"), 1).otherwise(0)).alias("total_reviews"),
            avg(when(col("is_review"), col("rating")).otherwise(None)).alias("avg_rating"),
            avg(when(col("is_review"), col("sentiment_score")).otherwise(None)).alias("avg_sentiment"),
            spark_sum(when(col("event_type") == "CART_ADD", 1).otherwise(0)).alias("cart_adds"),
            spark_sum(when(col("event_type") == "CART_REMOVE", 1).otherwise(0)).alias("cart_removes")
        )
        .withColumn("conversion_rate",
                   when(col("total_views") > 0,
                       col("total_purchases") / col("total_views"))
                   .otherwise(lit(0.0)))
        .withColumn("cart_abandonment_rate",
                   when(col("cart_adds") > 0,
                       (col("cart_adds") - col("total_purchases")) / col("cart_adds"))
                   .otherwise(lit(0.0)))
        .withColumn("processing_timestamp", current_timestamp())
    )
    
    return df_product

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write Gold Tables

# COMMAND ----------

def write_gold_table(df, table_name, partition_cols=None, merge_keys=None):
    """
    Write Gold table with merge logic for incremental updates.
    """
    if merge_keys:
        # Use merge for upsert
        if DeltaTable.isDeltaTable(spark, table_name):
            delta_table = DeltaTable.forName(spark, table_name)
            
            merge_condition = " AND ".join([f"target.{key} = source.{key}" for key in merge_keys])
            
            update_dict = {col: f"source.{col}" for col in df.columns if col not in merge_keys}
            
            (
                delta_table.alias("target")
                .merge(df.alias("source"), merge_condition)
                .whenMatchedUpdate(set=update_dict)
                .whenNotMatchedInsertAll()
                .execute()
            )
        else:
            # First write, create table
            (
                df.write
                .format("delta")
                .mode("overwrite")
                .option("overwriteSchema", "true")
                .saveAsTable(table_name)
            )
    else:
        # Simple append or overwrite
        (
            df.write
            .format("delta")
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .saveAsTable(table_name)
        )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Execute Gold Aggregations

# COMMAND ----------

# Read Silver data
df_silver = read_silver_data()

# Create Gold tables
print("Creating customer behavior daily aggregations...")
df_behavior = create_customer_behavior_daily(df_silver)
write_gold_table(
    df_behavior,
    gold_customer_behavior,
    partition_cols=["event_date"],
    merge_keys=["customer_id", "event_date"]
)

print("Creating sentiment summary...")
df_sentiment = create_sentiment_summary(df_silver)
write_gold_table(
    df_sentiment,
    gold_sentiment_summary,
    partition_cols=["date"],
    merge_keys=["date", "category", "customer_segment"]
)

print("Creating customer features...")
df_features = create_customer_features(df_silver)
write_gold_table(
    df_features,
    gold_customer_features,
    partition_cols=["event_date"],
    merge_keys=["customer_id", "event_date"]
)

print("Creating product performance...")
df_product = create_product_performance(df_silver)
write_gold_table(
    df_product,
    gold_product_performance,
    partition_cols=["date"],
    merge_keys=["product_id", "date"]
)

print("Gold layer aggregation complete!")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verification Queries

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Verify customer behavior table
# MAGIC SELECT 
# MAGIC   COUNT(*) as total_records,
# MAGIC   COUNT(DISTINCT customer_id) as unique_customers,
# MAGIC   MIN(event_date) as earliest_date,
# MAGIC   MAX(event_date) as latest_date,
# MAGIC   SUM(total_revenue) as total_revenue
# MAGIC FROM lakehouse.gold.customer_behavior_daily;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Top customers by revenue
# MAGIC SELECT 
# MAGIC   customer_id,
# MAGIC   SUM(total_revenue) as lifetime_revenue,
# MAGIC   SUM(total_purchases) as lifetime_purchases,
# MAGIC   AVG(conversion_rate) as avg_conversion_rate
# MAGIC FROM lakehouse.gold.customer_behavior_daily
# MAGIC GROUP BY customer_id
# MAGIC ORDER BY lifetime_revenue DESC
# MAGIC LIMIT 10;

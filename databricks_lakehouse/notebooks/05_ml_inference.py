# Databricks notebook source
# MAGIC %md
# MAGIC # Real-Time ML Inference Pipeline
# MAGIC 
# MAGIC This notebook implements real-time sentiment scoring using the trained model.
# MAGIC 
# MAGIC **Methods:**
# MAGIC - ai_query function (Databricks AI Functions)
# MAGIC - Model Serving endpoint
# MAGIC - Batch inference on Silver data

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

import json
import mlflow
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, expr, udf, when, lit, current_timestamp
)
from pyspark.sql.types import DoubleType, StringType
import requests

# Load configuration
workspace_config_path = "/Workspace/Shared/lakehouse/config/workspace_config.json"
with open(workspace_config_path, 'r') as f:
    ws_config = json.load(f)

catalog = ws_config["workspace"]["catalog"]
silver_table = f"{catalog}.silver.customer_events_cleaned"
silver_table_with_sentiment = f"{catalog}.silver.customer_events_with_sentiment"

# Model configuration
model_name = "customer_sentiment_classifier"
model_stage = "Production"  # or "Staging" for testing

# COMMAND ----------

# MAGIC %md
# MAGIC ## Method 1: Using ai_query (Databricks AI Functions)

# COMMAND ----------

def score_with_ai_query(df):
    """
    Score sentiment using Databricks ai_query function.
    This is the simplest method for real-time inference.
    """
    
    # Filter to reviews only
    df_reviews = df.filter(
        (col("is_review") == True) &
        (col("text_content") != "") &
        (col("text_content").isNotNull())
    )
    
    # Score using ai_query
    df_scored = df_reviews.withColumn(
        "sentiment_score",
        expr(f"ai_query('{model_name}', text_content)")
    )
    
    return df_scored

# COMMAND ----------

# MAGIC %md
# MAGIC ## Method 2: Using MLflow Model (Batch Inference)

# COMMAND ----------

def load_model_for_inference():
    """
    Load the registered MLflow model.
    """
    model_uri = f"models:/{model_name}/{model_stage}"
    model = mlflow.spark.load_model(model_uri)
    return model

# COMMAND ----------

def score_with_mlflow_model(df, model):
    """
    Score sentiment using loaded MLflow model.
    """
    # Prepare text column (same preprocessing as training)
    from pyspark.sql.functions import trim, lower, regexp_replace
    
    df_prepared = (
        df
        .filter(
            (col("is_review") == True) &
            (col("text_content") != "") &
            (col("text_content").isNotNull())
        )
        .withColumn(
            "text_cleaned",
            trim(lower(regexp_replace(col("text_content"), "[^a-zA-Z\\s]", "")))
        )
        .filter(length(col("text_cleaned")) >= 10)
    )
    
    # Make predictions
    predictions = model.transform(df_prepared)
    
    # Extract probability for positive class (index 1)
    df_scored = (
        predictions
        .withColumn(
            "sentiment_score",
            col("probability")[1]  # Probability of positive sentiment
        )
        .withColumn(
            "sentiment_label",
            when(col("prediction") == 1.0, "positive")
            .otherwise("negative")
        )
    )
    
    return df_scored

# COMMAND ----------

# MAGIC %md
# MAGIC ## Method 3: Using Model Serving Endpoint (REST API)

# COMMAND ----------

def create_serving_endpoint():
    """
    Create or update a Databricks Model Serving endpoint.
    """
    import requests
    import os
    
    workspace_url = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiUrl().get()
    token = dbutils.secrets.get(scope="databricks", key="api_token")
    
    endpoint_name = "customer-sentiment-endpoint"
    
    # Check if endpoint exists
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Create endpoint configuration
    endpoint_config = {
        "name": endpoint_name,
        "config": {
            "served_models": [
                {
                    "model_name": model_name,
                    "model_version": "latest",
                    "workload_size": "Small",
                    "scale_to_zero_enabled": True
                }
            ]
        }
    }
    
    # API call to create/update endpoint
    # Note: This is a simplified example - actual implementation depends on Databricks API version
    response = requests.post(
        f"{workspace_url}/api/2.0/serving-endpoints",
        headers=headers,
        json=endpoint_config
    )
    
    return endpoint_name

# COMMAND ----------

def score_with_serving_endpoint(df):
    """
    Score sentiment using Model Serving REST API.
    """
    import requests
    
    endpoint_url = dbutils.widgets.get("serving_endpoint_url") or "https://<workspace>.cloud.databricks.com/serving-endpoints/customer-sentiment-endpoint/invocations"
    token = dbutils.secrets.get(scope="databricks", key="api_token")
    
    def score_text(text):
        """
        UDF to call serving endpoint for each text.
        """
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "dataframe_records": [{"text_cleaned": text}]
        }
        
        try:
            response = requests.post(endpoint_url, headers=headers, json=payload, timeout=5)
            if response.status_code == 200:
                result = response.json()
                # Extract prediction probability
                return float(result["predictions"][0][1])  # Assuming probability of positive class
            else:
                return None
        except:
            return None
    
    # Register UDF
    score_udf = udf(score_text, DoubleType())
    
    # Apply scoring
    df_scored = (
        df
        .filter(
            (col("is_review") == True) &
            (col("text_content") != "") &
            (col("text_content").isNotNull())
        )
        .withColumn("sentiment_score", score_udf(col("text_content")))
    )
    
    return df_scored

# COMMAND ----------

# MAGIC %md
# MAGIC ## Real-Time Streaming Inference

# COMMAND ----------

def stream_inference_from_silver():
    """
    Stream inference on Silver layer data in real-time.
    """
    # Load model
    model = load_model_for_inference()
    
    # Read streaming from Silver
    df_silver_stream = (
        spark.readStream
        .table(silver_table)
        .filter(
            (col("is_review") == True) &
            (col("text_content") != "") &
            (col("sentiment_score").isNull())  # Only score unscored records
        )
    )
    
    # Score with model
    def score_batch(batch_df, batch_id):
        """
        Score each micro-batch.
        """
        if batch_df.count() > 0:
            scored_batch = score_with_mlflow_model(batch_df, model)
            
            # Write back to Silver with sentiment scores
            scored_batch.select(
                "event_id",
                "sentiment_score",
                "sentiment_label"
            ).write.format("delta").mode("append").saveAsTable(
                f"{catalog}.silver.sentiment_scores"
            )
    
    # Apply streaming inference
    query = (
        df_silver_stream.writeStream
        .foreachBatch(score_batch)
        .outputMode("update")
        .option("checkpointLocation", f"{ws_config['workspace']['checkpoint_root']}inference/sentiment")
        .trigger(processingTime='30 seconds')
        .start()
    )
    
    return query

# COMMAND ----------

# MAGIC %md
# MAGIC ## Merge Sentiment Scores Back to Silver

# COMMAND ----------

def merge_sentiment_to_silver():
    """
    Merge sentiment scores back into main Silver table.
    """
    from delta.tables import DeltaTable
    
    # Read sentiment scores
    df_scores = spark.table(f"{catalog}.silver.sentiment_scores")
    
    # Read Silver table
    silver_delta = DeltaTable.forName(spark, silver_table)
    
    # Merge
    (
        silver_delta.alias("target")
        .merge(
            df_scores.alias("source"),
            "target.event_id = source.event_id"
        )
        .whenMatchedUpdate(set={
            "sentiment_score": "source.sentiment_score",
            "sentiment_label": "source.sentiment_label"
        })
        .execute()
    )
    
    print("Sentiment scores merged to Silver table")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Execute Inference Pipeline

# COMMAND ----------

# Option 1: Batch inference on existing Silver data
print("Loading model...")
model = load_model_for_inference()

print("Reading Silver data...")
df_silver = spark.table(silver_table).limit(1000)  # Sample for testing

print("Scoring sentiment...")
df_scored = score_with_mlflow_model(df_silver, model)

print("Sample predictions:")
display(df_scored.select("event_id", "text_content", "sentiment_score", "sentiment_label").limit(10))

# Option 2: Start streaming inference
# streaming_query = stream_inference_from_silver()
# streaming_query.awaitTermination()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Inference Performance Metrics

# COMMAND ----------

def get_inference_metrics():
    """
    Calculate inference performance metrics.
    """
    df_scored = spark.table(silver_table).filter(col("sentiment_score").isNotNull())
    
    metrics = (
        df_scored
        .agg(
            count("*").alias("total_scored"),
            avg("sentiment_score").alias("avg_sentiment"),
            count(when(col("sentiment_label") == "positive", 1)).alias("positive_count"),
            count(when(col("sentiment_label") == "negative", 1)).alias("negative_count")
        )
    )
    
    return metrics

# Display metrics
inference_metrics = get_inference_metrics()
display(inference_metrics)

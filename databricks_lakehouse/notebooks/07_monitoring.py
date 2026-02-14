# Databricks notebook source
# MAGIC %md
# MAGIC # Monitoring & Alerting
# MAGIC 
# MAGIC This notebook implements comprehensive monitoring for:
# MAGIC - Streaming pipeline health
# MAGIC - Data quality metrics
# MAGIC - ML model performance
# MAGIC - SLA violations

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

import json
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, count, avg, max as spark_max, min as spark_min,
    current_timestamp, window, sum as spark_sum,
    when, countDistinct, stddev
)
from datetime import datetime, timedelta
import requests

# Load configuration
workspace_config_path = "/Workspace/Shared/lakehouse/config/workspace_config.json"
with open(workspace_config_path, 'r') as f:
    ws_config = json.load(f)

catalog = ws_config["workspace"]["catalog"]

# Alert thresholds
ALERT_THRESHOLDS = {
    "streaming_lag_seconds": 300,  # 5 minutes
    "data_quality_score": 0.8,
    "error_rate": 0.05,  # 5%
    "processing_throughput_min": 100  # records per minute
}

# COMMAND ----------

# MAGIC %md
# MAGIC ## Streaming Pipeline Monitoring

# COMMAND ----------

def get_streaming_metrics():
    """
    Get metrics from active streaming queries.
    """
    streams = spark.streams.active
    
    metrics = []
    for stream in streams:
        if stream.isActive:
            progress = stream.lastProgress
            metrics.append({
                "stream_id": stream.id,
                "name": stream.name,
                "is_active": True,
                "batch_id": progress.get("batchId"),
                "input_rows_per_second": progress.get("inputRowsPerSecond", 0),
                "processed_rows_per_second": progress.get("processedRowsPerSecond", 0),
                "num_input_rows": progress.get("numInputRows", 0),
                "timestamp": progress.get("timestamp"),
                "sources": progress.get("sources", []),
                "sink": progress.get("sink", {})
            })
    
    return metrics

# COMMAND ----------

def check_streaming_lag():
    """
    Check if streaming lag exceeds threshold.
    """
    metrics = get_streaming_metrics()
    
    alerts = []
    for metric in metrics:
        # Calculate lag (simplified - actual lag depends on source)
        # In production, compare latest processed timestamp with current time
        if metric["input_rows_per_second"] == 0 and metric["num_input_rows"] > 0:
            alerts.append({
                "stream_id": metric["stream_id"],
                "alert_type": "STREAMING_LAG",
                "message": f"Stream {metric['name']} has no input throughput",
                "severity": "WARNING"
            })
    
    return alerts

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Quality Monitoring

# COMMAND ----------

def monitor_bronze_quality():
    """
    Monitor data quality in Bronze layer.
    """
    df_bronze = spark.table(f"{catalog}.bronze.customer_events_raw")
    
    # Get recent data (last hour)
    one_hour_ago = datetime.now() - timedelta(hours=1)
    
    df_recent = df_bronze.filter(col("ingestion_timestamp") >= one_hour_ago)
    
    metrics = (
        df_recent
        .agg(
            count("*").alias("total_records"),
            avg("quality_score").alias("avg_quality_score"),
            spark_sum(when(col("is_valid") == False, 1).otherwise(0)).alias("invalid_records"),
            countDistinct("event_id").alias("unique_events"),
            count("*") - countDistinct("event_id").alias("duplicate_events")
        )
    )
    
    result = metrics.collect()[0]
    
    # Check thresholds
    alerts = []
    if result["avg_quality_score"] < ALERT_THRESHOLDS["data_quality_score"]:
        alerts.append({
            "layer": "bronze",
            "alert_type": "DATA_QUALITY",
            "metric": "avg_quality_score",
            "value": result["avg_quality_score"],
            "threshold": ALERT_THRESHOLDS["data_quality_score"],
            "severity": "CRITICAL"
        })
    
    error_rate = result["invalid_records"] / result["total_records"] if result["total_records"] > 0 else 0
    if error_rate > ALERT_THRESHOLDS["error_rate"]:
        alerts.append({
            "layer": "bronze",
            "alert_type": "ERROR_RATE",
            "metric": "error_rate",
            "value": error_rate,
            "threshold": ALERT_THRESHOLDS["error_rate"],
            "severity": "WARNING"
        })
    
    return result, alerts

# COMMAND ----------

def monitor_silver_quality():
    """
    Monitor data quality in Silver layer.
    """
    df_silver = spark.table(f"{catalog}.silver.customer_events_cleaned")
    
    # Get recent data
    one_hour_ago = datetime.now() - timedelta(hours=1)
    
    df_recent = df_silver.filter(col("processing_timestamp") >= one_hour_ago)
    
    metrics = (
        df_recent
        .agg(
            count("*").alias("total_records"),
            avg("quality_score").alias("avg_quality_score"),
            spark_sum(when(col("is_high_quality") == False, 1).otherwise(0)).alias("low_quality_records"),
            spark_sum(when(col("is_valid_event_type") == False, 1).otherwise(0)).alias("invalid_event_types"),
            spark_sum(when(col("is_data_valid") == False, 1).otherwise(0)).alias("invalid_data_records")
        )
    )
    
    result = metrics.collect()[0]
    
    alerts = []
    if result["avg_quality_score"] < ALERT_THRESHOLDS["data_quality_score"]:
        alerts.append({
            "layer": "silver",
            "alert_type": "DATA_QUALITY",
            "metric": "avg_quality_score",
            "value": result["avg_quality_score"],
            "threshold": ALERT_THRESHOLDS["data_quality_score"],
            "severity": "CRITICAL"
        })
    
    return result, alerts

# COMMAND ----------

def monitor_gold_completeness():
    """
    Monitor Gold layer data completeness and freshness.
    """
    df_gold = spark.table(f"{catalog}.gold.customer_behavior_daily")
    
    # Check latest date
    latest_date = df_gold.agg(spark_max("event_date")).collect()[0][0]
    days_behind = (datetime.now().date() - latest_date).days if latest_date else 999
    
    metrics = {
        "latest_date": latest_date,
        "days_behind": days_behind,
        "total_records": df_gold.count(),
        "unique_customers": df_gold.select("customer_id").distinct().count()
    }
    
    alerts = []
    if days_behind > 1:
        alerts.append({
            "layer": "gold",
            "alert_type": "DATA_FRESHNESS",
            "metric": "days_behind",
            "value": days_behind,
            "threshold": 1,
            "severity": "WARNING",
            "message": f"Gold layer is {days_behind} days behind"
        })
    
    return metrics, alerts

# COMMAND ----------

# MAGIC %md
# MAGIC ## ML Model Performance Monitoring

# COMMAND ----------

def monitor_ml_model_performance():
    """
    Monitor ML model performance metrics.
    """
    import mlflow
    from mlflow.tracking import MlflowClient
    
    client = MlflowClient()
    model_name = "customer_sentiment_classifier"
    
    # Get latest production model
    try:
        latest_version = client.get_latest_versions(model_name, stages=["Production"])[0]
        model_version = latest_version.version
        
        # Get model metrics from MLflow
        run = client.get_run(latest_version.run_id)
        metrics = {
            "model_name": model_name,
            "version": model_version,
            "test_auc": run.data.metrics.get("test_auc", 0),
            "test_accuracy": run.data.metrics.get("test_accuracy", 0),
            "stage": "Production"
        }
        
        # Check for model drift (simplified - compare current predictions with historical)
        df_silver = spark.table(f"{catalog}.silver.customer_events_cleaned")
        df_recent = df_silver.filter(
            (col("sentiment_score").isNotNull()) &
            (col("processing_timestamp") >= datetime.now() - timedelta(days=7))
        )
        
        if df_recent.count() > 0:
            avg_sentiment = df_recent.agg(avg("sentiment_score")).collect()[0][0]
            metrics["recent_avg_sentiment"] = avg_sentiment
            
            # Compare with historical baseline (simplified)
            # In production, use more sophisticated drift detection
            baseline_sentiment = 0.6  # Example baseline
            drift = abs(avg_sentiment - baseline_sentiment)
            
            alerts = []
            if drift > 0.15:  # 15% drift threshold
                alerts.append({
                    "alert_type": "MODEL_DRIFT",
                    "metric": "sentiment_drift",
                    "value": drift,
                    "threshold": 0.15,
                    "severity": "WARNING",
                    "message": f"Model predictions show {drift:.2%} drift from baseline"
                })
        else:
            alerts = []
        
        return metrics, alerts
        
    except Exception as e:
        return {"error": str(e)}, [{
            "alert_type": "MODEL_MONITORING_ERROR",
            "severity": "ERROR",
            "message": f"Failed to monitor model: {str(e)}"
        }]

# COMMAND ----------

# MAGIC %md
# MAGIC ## Processing Throughput Monitoring

# COMMAND ----------

def monitor_processing_throughput():
    """
    Monitor processing throughput across layers.
    """
    # Bronze throughput
    df_bronze = spark.table(f"{catalog}.bronze.customer_events_raw")
    bronze_recent = df_bronze.filter(
        col("ingestion_timestamp") >= datetime.now() - timedelta(hours=1)
    )
    bronze_count = bronze_recent.count()
    bronze_throughput = bronze_count / 60  # records per minute
    
    # Silver throughput
    df_silver = spark.table(f"{catalog}.silver.customer_events_cleaned")
    silver_recent = df_silver.filter(
        col("processing_timestamp") >= datetime.now() - timedelta(hours=1)
    )
    silver_count = silver_recent.count()
    silver_throughput = silver_count / 60
    
    metrics = {
        "bronze_throughput_per_min": bronze_throughput,
        "silver_throughput_per_min": silver_throughput,
        "bronze_total_last_hour": bronze_count,
        "silver_total_last_hour": silver_count
    }
    
    alerts = []
    if bronze_throughput < ALERT_THRESHOLDS["processing_throughput_min"]:
        alerts.append({
            "alert_type": "LOW_THROUGHPUT",
            "layer": "bronze",
            "metric": "throughput_per_min",
            "value": bronze_throughput,
            "threshold": ALERT_THRESHOLDS["processing_throughput_min"],
            "severity": "WARNING"
        })
    
    return metrics, alerts

# COMMAND ----------

# MAGIC %md
# MAGIC ## Alerting System

# COMMAND ----------

def send_alert(alert):
    """
    Send alert via email, Slack, PagerDuty, etc.
    """
    # Example: Send to Databricks SQL alerts
    # In production, integrate with your alerting system
    
    alert_message = f"""
    Alert Type: {alert['alert_type']}
    Severity: {alert['severity']}
    Layer: {alert.get('layer', 'N/A')}
    Metric: {alert.get('metric', 'N/A')}
    Value: {alert.get('value', 'N/A')}
    Threshold: {alert.get('threshold', 'N/A')}
    Message: {alert.get('message', '')}
    Timestamp: {datetime.now()}
    """
    
    print(f"ALERT: {alert_message}")
    
    # Example: Write to alert table for dashboard
    alert_df = spark.createDataFrame([{
        "alert_id": f"{alert['alert_type']}_{datetime.now().timestamp()}",
        "alert_type": alert['alert_type'],
        "severity": alert['severity'],
        "layer": alert.get('layer'),
        "metric": alert.get('metric'),
        "value": alert.get('value'),
        "threshold": alert.get('threshold'),
        "message": alert.get('message', ''),
        "timestamp": datetime.now()
    }])
    
    # Write to alert table (create if not exists)
    try:
        alert_df.write.format("delta").mode("append").saveAsTable(
            f"{catalog}.monitoring.alerts"
        )
    except:
        # Create table if it doesn't exist
        alert_df.write.format("delta").mode("overwrite").saveAsTable(
            f"{catalog}.monitoring.alerts"
        )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Comprehensive Monitoring Dashboard

# COMMAND ----------

def run_comprehensive_monitoring():
    """
    Run all monitoring checks and generate alerts.
    """
    all_alerts = []
    all_metrics = {}
    
    print("=" * 50)
    print("MONITORING REPORT")
    print("=" * 50)
    print(f"Timestamp: {datetime.now()}\n")
    
    # Streaming metrics
    print("1. Streaming Pipeline Health")
    print("-" * 50)
    stream_metrics = get_streaming_metrics()
    print(f"Active streams: {len(stream_metrics)}")
    for metric in stream_metrics:
        print(f"  Stream {metric['name']}: {metric['input_rows_per_second']:.2f} rows/sec")
    stream_alerts = check_streaming_lag()
    all_alerts.extend(stream_alerts)
    all_metrics["streaming"] = stream_metrics
    print()
    
    # Bronze quality
    print("2. Bronze Layer Quality")
    print("-" * 50)
    bronze_metrics, bronze_alerts = monitor_bronze_quality()
    print(f"Total records: {bronze_metrics['total_records']}")
    print(f"Avg quality score: {bronze_metrics['avg_quality_score']:.3f}")
    print(f"Invalid records: {bronze_metrics['invalid_records']}")
    all_alerts.extend(bronze_alerts)
    all_metrics["bronze"] = bronze_metrics.asDict()
    print()
    
    # Silver quality
    print("3. Silver Layer Quality")
    print("-" * 50)
    silver_metrics, silver_alerts = monitor_silver_quality()
    print(f"Total records: {silver_metrics['total_records']}")
    print(f"Avg quality score: {silver_metrics['avg_quality_score']:.3f}")
    all_alerts.extend(silver_alerts)
    all_metrics["silver"] = silver_metrics.asDict()
    print()
    
    # Gold completeness
    print("4. Gold Layer Completeness")
    print("-" * 50)
    gold_metrics, gold_alerts = monitor_gold_completeness()
    print(f"Latest date: {gold_metrics['latest_date']}")
    print(f"Days behind: {gold_metrics['days_behind']}")
    all_alerts.extend(gold_alerts)
    all_metrics["gold"] = gold_metrics
    print()
    
    # ML model
    print("5. ML Model Performance")
    print("-" * 50)
    ml_metrics, ml_alerts = monitor_ml_model_performance()
    if "error" not in ml_metrics:
        print(f"Model: {ml_metrics['model_name']} v{ml_metrics['version']}")
        print(f"Test AUC: {ml_metrics['test_auc']:.3f}")
        print(f"Test Accuracy: {ml_metrics['test_accuracy']:.3f}")
    all_alerts.extend(ml_alerts)
    all_metrics["ml"] = ml_metrics
    print()
    
    # Throughput
    print("6. Processing Throughput")
    print("-" * 50)
    throughput_metrics, throughput_alerts = monitor_processing_throughput()
    print(f"Bronze: {throughput_metrics['bronze_throughput_per_min']:.1f} records/min")
    print(f"Silver: {throughput_metrics['silver_throughput_per_min']:.1f} records/min")
    all_alerts.extend(throughput_alerts)
    all_metrics["throughput"] = throughput_metrics
    print()
    
    # Alerts summary
    print("=" * 50)
    print("ALERTS SUMMARY")
    print("=" * 50)
    if all_alerts:
        critical = [a for a in all_alerts if a.get("severity") == "CRITICAL"]
        warnings = [a for a in all_alerts if a.get("severity") == "WARNING"]
        
        print(f"Critical: {len(critical)}")
        print(f"Warnings: {len(warnings)}")
        
        for alert in critical + warnings:
            send_alert(alert)
            print(f"\n{alert['severity']}: {alert['alert_type']}")
            print(f"  {alert.get('message', '')}")
    else:
        print("No alerts - all systems healthy!")
    
    return all_metrics, all_alerts

# COMMAND ----------

# MAGIC %md
# MAGIC ## Execute Monitoring

# COMMAND ----------

# Run comprehensive monitoring
metrics, alerts = run_comprehensive_monitoring()

# Store metrics for dashboard
metrics_df = spark.createDataFrame([{
    "timestamp": datetime.now(),
    "metrics": json.dumps(metrics),
    "alert_count": len(alerts)
}])

try:
    metrics_df.write.format("delta").mode("append").saveAsTable(
        f"{catalog}.monitoring.metrics"
    )
except:
    metrics_df.write.format("delta").mode("overwrite").saveAsTable(
        f"{catalog}.monitoring.metrics"
    )

# Databricks notebook source
# MAGIC %md
# MAGIC # Performance Optimization
# MAGIC 
# MAGIC This notebook implements comprehensive performance optimization techniques for the lakehouse.
# MAGIC 
# MAGIC **Optimizations:**
# MAGIC - Delta Lake OPTIMIZE and Z-ordering
# MAGIC - Bloom filter creation
# MAGIC - Table statistics and monitoring
# MAGIC - Spark configuration tuning
# MAGIC - Automated optimization routines

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

import json
from pyspark.sql import SparkSession
from utils.performance_optimizer import (
    DeltaTableOptimizer, 
    SparkConfigOptimizer,
    optimize_table_routine
)

# Load configuration
workspace_config_path = "/Workspace/Shared/lakehouse/config/workspace_config.json"
with open(workspace_config_path, 'r') as f:
    ws_config = json.load(f)

catalog = ws_config["workspace"]["catalog"]

# COMMAND ----------

# MAGIC %md
# MAGIC ## Apply Spark Optimizations

# COMMAND ----------

# Initialize optimizer
spark_optimizer = SparkConfigOptimizer(spark)

# Apply all optimizations
spark_optimizer.apply_all_optimizations(
    num_shuffle_partitions=200,
    enable_cache=True
)

print("Spark performance optimizations applied!")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Optimize Bronze Table

# COMMAND ----------

bronze_table = f"{catalog}.bronze.customer_events_raw"
bronze_optimizer = DeltaTableOptimizer(spark)

# Get current stats
bronze_stats_before = bronze_optimizer.get_table_stats(bronze_table)
print("Bronze table stats (before):")
print(json.dumps(bronze_stats_before, indent=2))

# Optimize (no Z-ordering for raw data)
bronze_result = bronze_optimizer.optimize_table(bronze_table)
print("\nOptimization result:")
print(json.dumps(bronze_result, indent=2))

# Get stats after
bronze_stats_after = bronze_optimizer.get_table_stats(bronze_table)
print("\nBronze table stats (after):")
print(json.dumps(bronze_stats_after, indent=2))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Optimize Silver Table with Z-Ordering

# COMMAND ----------

silver_table = f"{catalog}.silver.customer_events_cleaned"
silver_optimizer = DeltaTableOptimizer(spark)

# Get current stats
silver_stats_before = silver_optimizer.get_table_stats(silver_table)
print("Silver table stats (before):")
print(json.dumps(silver_stats_before, indent=2))

# Optimize with Z-ordering on frequently filtered columns
silver_result = silver_optimizer.optimize_table(
    silver_table,
    z_order_cols=["customer_id", "event_date", "event_type"]
)
print("\nOptimization result:")
print(json.dumps(silver_result, indent=2))

# Create bloom filter for fast customer lookups
bloom_result = silver_optimizer.create_bloom_filter(
    silver_table,
    columns=["customer_id", "event_id"],
    fpp=0.1,
    num_items=10000000
)
print("\nBloom filter creation result:")
print(json.dumps(bloom_result, indent=2))

# Get stats after
silver_stats_after = silver_optimizer.get_table_stats(silver_table)
print("\nSilver table stats (after):")
print(json.dumps(silver_stats_after, indent=2))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Optimize Gold Tables

# COMMAND ----------

gold_tables = {
    "customer_behavior_daily": {
        "table": f"{catalog}.gold.customer_behavior_daily",
        "z_order_cols": ["customer_id", "event_date"],
        "partition_filter": "event_date >= CURRENT_DATE() - INTERVAL 30 DAYS"
    },
    "sentiment_summary": {
        "table": f"{catalog}.gold.sentiment_summary",
        "z_order_cols": ["date", "category"],
        "partition_filter": "date >= CURRENT_DATE() - INTERVAL 30 DAYS"
    },
    "customer_features": {
        "table": f"{catalog}.gold.customer_features",
        "z_order_cols": ["customer_id", "event_date"]
    },
    "product_performance": {
        "table": f"{catalog}.gold.product_performance",
        "z_order_cols": ["product_id", "date", "category"]
    }
}

gold_optimizer = DeltaTableOptimizer(spark)

for table_name, config in gold_tables.items():
    print(f"\n{'='*60}")
    print(f"Optimizing {table_name}")
    print(f"{'='*60}")
    
    # Get stats before
    stats_before = gold_optimizer.get_table_stats(config["table"])
    print(f"Files before: {stats_before.get('num_files', 0)}")
    print(f"Size before: {stats_before.get('size_gb', 0):.2f} GB")
    
    # Optimize
    result = gold_optimizer.optimize_table(
        config["table"],
        partition_filter=config.get("partition_filter"),
        z_order_cols=config.get("z_order_cols")
    )
    
    print(f"Files removed: {result.get('files_removed', 0)}")
    print(f"Files added: {result.get('files_added', 0)}")
    
    # Get stats after
    stats_after = gold_optimizer.get_table_stats(config["table"])
    print(f"Files after: {stats_after.get('num_files', 0)}")
    print(f"Size after: {stats_after.get('size_gb', 0):.2f} GB")
    
    # Calculate improvement
    if stats_before.get('num_files', 0) > 0:
        file_reduction = (1 - stats_after.get('num_files', 0) / stats_before.get('num_files', 1)) * 100
        print(f"File reduction: {file_reduction:.1f}%")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Bloom Filters for High-Cardinality Lookups

# COMMAND ----------

# Create bloom filters on frequently joined/looked-up columns
bloom_configs = [
    {
        "table": f"{catalog}.silver.customer_events_cleaned",
        "columns": ["customer_id", "event_id"],
        "num_items": 10000000
    },
    {
        "table": f"{catalog}.gold.customer_behavior_daily",
        "columns": ["customer_id"],
        "num_items": 1000000
    },
    {
        "table": f"{catalog}.gold.product_performance",
        "columns": ["product_id"],
        "num_items": 100000
    }
]

for config in bloom_configs:
    print(f"\nCreating bloom filter on {config['table']} for columns: {config['columns']}")
    result = silver_optimizer.create_bloom_filter(
        config["table"],
        columns=config["columns"],
        num_items=config["num_items"]
    )
    print(f"Status: {result.get('status', 'unknown')}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## VACUUM Old Files

# COMMAND ----------

# Vacuum Bronze (retain 90 days)
bronze_vacuum = bronze_optimizer.vacuum_table(
    bronze_table,
    retention_hours=90 * 24
)
print("Bronze VACUUM result:")
print(json.dumps(bronze_vacuum, indent=2))

# Vacuum Silver (retain 180 days)
silver_vacuum = silver_optimizer.vacuum_table(
    silver_table,
    retention_hours=180 * 24
)
print("\nSilver VACUUM result:")
print(json.dumps(silver_vacuum, indent=2))

# Vacuum Gold (retain 365 days - keep longer for analytics)
for table_name, config in gold_tables.items():
    gold_vacuum = gold_optimizer.vacuum_table(
        config["table"],
        retention_hours=365 * 24
    )
    print(f"\n{table_name} VACUUM result:")
    print(json.dumps(gold_vacuum, indent=2))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Performance Comparison

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Compare query performance before and after optimization
# MAGIC -- Run this query and note the execution time
# MAGIC 
# MAGIC EXPLAIN EXTENDED
# MAGIC SELECT 
# MAGIC   customer_id,
# MAGIC   SUM(total_revenue) as lifetime_revenue,
# MAGIC   AVG(conversion_rate) as avg_conversion
# MAGIC FROM lakehouse.gold.customer_behavior_daily
# MAGIC WHERE event_date >= CURRENT_DATE() - INTERVAL 30 DAYS
# MAGIC   AND customer_id IN ('cust_001', 'cust_002', 'cust_003')
# MAGIC GROUP BY customer_id;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Automated Optimization Routine

# COMMAND ----------

def run_optimization_routine():
    """
    Run complete optimization routine for all tables.
    """
    tables_to_optimize = [
        {
            "table": f"{catalog}.bronze.customer_events_raw",
            "z_order_cols": None
        },
        {
            "table": f"{catalog}.silver.customer_events_cleaned",
            "z_order_cols": ["customer_id", "event_date", "event_type"]
        },
        {
            "table": f"{catalog}.gold.customer_behavior_daily",
            "z_order_cols": ["customer_id", "event_date"]
        },
        {
            "table": f"{catalog}.gold.sentiment_summary",
            "z_order_cols": ["date", "category"]
        },
        {
            "table": f"{catalog}.gold.customer_features",
            "z_order_cols": ["customer_id", "event_date"]
        },
        {
            "table": f"{catalog}.gold.product_performance",
            "z_order_cols": ["product_id", "date"]
        }
    ]
    
    results = []
    for config in tables_to_optimize:
        result = optimize_table_routine(
            spark,
            config["table"],
            z_order_cols=config.get("z_order_cols"),
            vacuum_retention_hours=168  # 7 days default
        )
        results.append(result)
    
    return results

# Run optimization routine
# optimization_results = run_optimization_routine()
# print("Optimization routine completed!")
# print(json.dumps(optimization_results, indent=2, default=str))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Table Statistics Summary

# COMMAND ----------

# Get statistics for all tables
all_tables = [
    f"{catalog}.bronze.customer_events_raw",
    f"{catalog}.silver.customer_events_cleaned",
    f"{catalog}.gold.customer_behavior_daily",
    f"{catalog}.gold.sentiment_summary",
    f"{catalog}.gold.customer_features",
    f"{catalog}.gold.product_performance"
]

print("Table Statistics Summary")
print("=" * 80)

for table in all_tables:
    stats = silver_optimizer.get_table_stats(table)
    if "error" not in stats:
        print(f"\n{table}")
        print(f"  Size: {stats.get('size_gb', 0):.2f} GB")
        print(f"  Files: {stats.get('num_files', 0)}")
        print(f"  Partitions: {stats.get('num_partitions', 0)}")
        if stats.get('avg_file_size_mb', 0) > 0:
            print(f"  Avg File Size: {stats.get('avg_file_size_mb', 0):.2f} MB")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Performance Monitoring

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Monitor Delta table history for optimization runs
# MAGIC SELECT 
# MAGIC   timestamp,
# MAGIC   operation,
# MAGIC   operationParameters,
# MAGIC   operationMetrics
# MAGIC FROM (
# MAGIC   DESCRIBE HISTORY lakehouse.silver.customer_events_cleaned
# MAGIC )
# MAGIC WHERE operation = 'OPTIMIZE'
# MAGIC ORDER BY timestamp DESC
# MAGIC LIMIT 10;

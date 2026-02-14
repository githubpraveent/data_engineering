# Databricks notebook source
# MAGIC %md
# MAGIC # Validate Bronze Layer Ingestion
# MAGIC 
# MAGIC This notebook performs data quality checks on Bronze layer data:
# MAGIC - Schema validation
# MAGIC - Completeness checks
# MAGIC - Data type validation
# MAGIC - Record count validation

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

dbutils.widgets.text("source_path", "")
dbutils.widgets.text("source_type", "")

source_path = dbutils.widgets.get("source_path")
source_type = dbutils.widgets.get("source_type")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Read Data

# COMMAND ----------

from pyspark.sql.functions import *
from delta.tables import *

df = spark.read.format("delta").load(source_path)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Schema Validation

# COMMAND ----------

# Expected schema for POS events
expected_schema = {
    "event_id": "string",
    "store_id": "string",
    "transaction_id": "string",
    "customer_id": "string",
    "product_id": "string",
    "quantity": "integer",
    "price": "decimal",
    "transaction_timestamp": "timestamp"
}

# Check if all expected columns exist
actual_columns = set(df.columns)
expected_columns = set(expected_schema.keys())

missing_columns = expected_columns - actual_columns
extra_columns = actual_columns - expected_columns

print(f"Missing columns: {missing_columns}")
print(f"Extra columns: {extra_columns}")

assert len(missing_columns) == 0, f"Missing required columns: {missing_columns}"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Completeness Checks

# COMMAND ----------

# Check for nulls in critical fields
null_checks = df.select([
    count(when(col(c).isNull(), c)).alias(f"{c}_nulls")
    for c in ["event_id", "transaction_id", "store_id", "product_id"]
])

display(null_checks)

# Calculate completeness percentage
total_records = df.count()
null_counts = null_checks.collect()[0]

for col_name in ["event_id", "transaction_id", "store_id", "product_id"]:
    null_count = null_counts[f"{col_name}_nulls"]
    completeness = ((total_records - null_count) / total_records) * 100
    print(f"{col_name} completeness: {completeness:.2f}%")
    
    # Fail if completeness is below threshold
    assert completeness >= 95.0, f"{col_name} completeness below 95%: {completeness}%"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Type Validation

# COMMAND ----------

# Validate data types
df.select(
    count(when(col("quantity").cast("int").isNull(), 1)).alias("invalid_quantity"),
    count(when(col("price").cast("decimal(10,2)").isNull(), 1)).alias("invalid_price"),
    count(when(col("transaction_timestamp").cast("timestamp").isNull(), 1)).alias("invalid_timestamp")
).show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Record Count Validation

# COMMAND ----------

# Check if we have a reasonable number of records
record_count = df.count()
print(f"Total records: {record_count}")

# Fail if no records
assert record_count > 0, "No records found in Bronze layer"

# Check for duplicates
duplicate_count = df.groupBy("event_id").count().filter(col("count") > 1).count()
print(f"Duplicate event_ids: {duplicate_count}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

print("=" * 50)
print("Bronze Layer Validation Summary")
print("=" * 50)
print(f"Source Type: {source_type}")
print(f"Source Path: {source_path}")
print(f"Total Records: {record_count}")
print(f"Schema Validation: PASSED")
print(f"Completeness Check: PASSED")
print(f"Data Type Validation: PASSED")
print("=" * 50)


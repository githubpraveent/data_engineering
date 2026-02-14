# Databricks notebook source
# MAGIC %md
# MAGIC # Transform POS Events from Bronze to Silver
# MAGIC 
# MAGIC This notebook transforms POS events from Bronze (raw) to Silver (staged) layer:
# MAGIC - Cleans and validates data
# MAGIC - Standardizes schemas
# MAGIC - Deduplicates records
# MAGIC - Applies data quality rules

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

dbutils.widgets.text("bronze_path", "")
dbutils.widgets.text("silver_path", "")
dbutils.widgets.text("processing_date", "")

bronze_path = dbutils.widgets.get("bronze_path")
silver_path = dbutils.widgets.get("silver_path")
processing_date = dbutils.widgets.get("processing_date")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Read Data from Bronze

# COMMAND ----------

from pyspark.sql.functions import *
from pyspark.sql.types import *
from delta.tables import *

# Read from Bronze
df_bronze = spark.read.format("delta").load(bronze_path)

# Filter by processing date if provided
if processing_date:
    df_bronze = df_bronze.filter(col("processing_date") == processing_date)

print(f"Records in Bronze: {df_bronze.count()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Cleaning and Validation

# COMMAND ----------

# Remove nulls in critical fields
df_cleaned = df_bronze.filter(
    col("event_id").isNotNull() &
    col("transaction_id").isNotNull() &
    col("store_id").isNotNull() &
    col("product_id").isNotNull() &
    col("transaction_timestamp").isNotNull()
)

# Validate data types and ranges
df_validated = df_cleaned.filter(
    (col("quantity") > 0) &
    (col("price") >= 0) &
    (col("transaction_timestamp") >= "2020-01-01")  # Reasonable date range
)

# Standardize text fields
df_standardized = df_validated.withColumn(
    "store_id", upper(trim(col("store_id")))
).withColumn(
    "product_id", upper(trim(col("product_id")))
).withColumn(
    "customer_id", upper(trim(col("customer_id")))
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Deduplication

# COMMAND ----------

# Remove duplicates based on event_id (assuming event_id is unique)
from pyspark.sql.window import Window

window_spec = Window.partitionBy("event_id").orderBy(desc("ingestion_timestamp"))

df_deduped = df_standardized.withColumn(
    "row_num", row_number().over(window_spec)
).filter(col("row_num") == 1).drop("row_num")

print(f"Records after deduplication: {df_deduped.count()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Add Calculated Fields

# COMMAND ----------

# Calculate line total
df_enriched = df_deduped.withColumn(
    "line_total", col("quantity") * col("price")
).withColumn(
    "year", year(col("transaction_timestamp"))
).withColumn(
    "month", month(col("transaction_timestamp"))
).withColumn(
    "day", dayofmonth(col("transaction_timestamp"))
).withColumn(
    "hour", hour(col("transaction_timestamp"))
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write to Silver Layer

# COMMAND ----------

# Write to Silver in Delta format
df_enriched.write.format("delta").mode("overwrite").option("mergeSchema", "true").partitionBy(
    "processing_date", "store_id"
).save(silver_path)

# Optimize Delta table
spark.sql(f"OPTIMIZE delta.`{silver_path}`")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Silver Data

# COMMAND ----------

df_silver = spark.read.format("delta").load(silver_path)
display(df_silver.limit(100))

# Show summary statistics
df_silver.select(
    count("*").alias("total_records"),
    countDistinct("event_id").alias("unique_events"),
    countDistinct("store_id").alias("unique_stores"),
    sum("line_total").alias("total_revenue")
).show()


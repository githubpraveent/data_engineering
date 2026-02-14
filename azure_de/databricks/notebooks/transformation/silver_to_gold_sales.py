# Databricks notebook source
# MAGIC %md
# MAGIC # Transform to Gold Layer - Sales Fact
# MAGIC 
# MAGIC This notebook creates the curated sales fact table in the Gold layer:
# MAGIC - Joins POS events with customer, product, and store data
# MAGIC - Applies business logic
# MAGIC - Creates aggregated and enriched sales facts

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

dbutils.widgets.text("silver_path", "")
dbutils.widgets.text("gold_path", "")
dbutils.widgets.text("processing_date", "")

silver_path = dbutils.widgets.get("silver_path")
gold_path = dbutils.widgets.get("gold_path")
processing_date = dbutils.widgets.get("processing_date")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Read Silver Layer Data

# COMMAND ----------

from pyspark.sql.functions import *
from delta.tables import *

# Read POS events from Silver
df_pos = spark.read.format("delta").load(f"{silver_path}/pos/events/")

if processing_date:
    df_pos = df_pos.filter(col("processing_date") == processing_date)

# Read other Silver tables (if available)
# df_customers = spark.read.format("delta").load(f"{silver_path}/customers/")
# df_products = spark.read.format("delta").load(f"{silver_path}/products/")
# df_stores = spark.read.format("delta").load(f"{silver_path}/stores/")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Sales Fact

# COMMAND ----------

# Aggregate POS events to transaction level
df_sales_fact = df_pos.groupBy(
    "transaction_id",
    "store_id",
    "customer_id",
    "transaction_timestamp",
    "processing_date"
).agg(
    sum("quantity").alias("total_quantity"),
    sum("line_total").alias("total_amount"),
    count("*").alias("line_item_count"),
    min("product_id").alias("first_product_id"),  # Example aggregation
    max("product_id").alias("last_product_id")
).withColumn(
    "transaction_date", to_date(col("transaction_timestamp"))
).withColumn(
    "transaction_hour", hour(col("transaction_timestamp"))
).withColumn(
    "transaction_day_of_week", dayofweek(col("transaction_timestamp"))
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Apply Business Logic

# COMMAND ----------

# Add business rules
df_sales_fact = df_sales_fact.withColumn(
    "transaction_type",
    when(col("total_amount") >= 100, "High Value")
    .when(col("total_amount") >= 50, "Medium Value")
    .otherwise("Low Value")
).withColumn(
    "is_weekend",
    when(col("transaction_day_of_week").isin([1, 7]), True)
    .otherwise(False)
).withColumn(
    "is_business_hours",
    when((col("transaction_hour") >= 9) & (col("transaction_hour") <= 17), True)
    .otherwise(False)
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Add Surrogate Keys (for warehouse loading)

# COMMAND ----------

# Generate surrogate keys (these would typically come from dimension tables)
from pyspark.sql.functions import monotonically_increasing_id

df_sales_fact = df_sales_fact.withColumn(
    "sales_fact_key", monotonically_increasing_id()
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write to Gold Layer

# COMMAND ----------

# Write to Gold in Delta format
df_sales_fact.write.format("delta").mode("overwrite").option("mergeSchema", "true").partitionBy(
    "processing_date", "store_id"
).save(f"{gold_path}/sales_fact/")

# Optimize Delta table
spark.sql(f"OPTIMIZE delta.`{gold_path}/sales_fact/`")

# Create Delta table for easier querying
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS gold.sales_fact
    USING DELTA
    LOCATION '{gold_path}/sales_fact/'
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Gold Data

# COMMAND ----------

df_gold = spark.read.format("delta").load(f"{gold_path}/sales_fact/")
display(df_gold.limit(100))

# Show summary
df_gold.select(
    count("*").alias("total_transactions"),
    sum("total_amount").alias("total_revenue"),
    avg("total_amount").alias("avg_transaction_value"),
    countDistinct("store_id").alias("unique_stores"),
    countDistinct("customer_id").alias("unique_customers")
).show()


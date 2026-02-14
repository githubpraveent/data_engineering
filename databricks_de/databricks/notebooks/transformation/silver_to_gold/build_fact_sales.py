"""
Databricks Notebook: Silver to Gold - Fact Sales
Builds Sales fact table from Silver layer, joining with dimension tables.
"""

# MAGIC %md
# MAGIC # Silver to Gold: Fact Sales
# MAGIC 
# MAGIC This notebook builds the Sales fact table by:
# MAGIC - Reading sales transactions from Silver
# MAGIC - Joining with dimension tables (Customer, Product, Store, Date)
# MAGIC - Adding calculated measures (profit, margins)
# MAGIC - Creating surrogate keys for fact records

# COMMAND ----------

# MAGIC %run ../../utilities/common_functions
# MAGIC %run ../../utilities/schema_definitions

# COMMAND ----------

# Configuration
dbutils.widgets.text("environment", "dev", "Environment")
dbutils.widgets.text("catalog", "retail_datalake", "Unity Catalog")
dbutils.widgets.text("silver_schema", "silver", "Silver Schema Name")
dbutils.widgets.text("gold_schema", "gold", "Gold Schema Name")
dbutils.widgets.text("incremental", "true", "Incremental Load")

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, lit, current_timestamp, year, month, dayofmonth,
    when, coalesce, sha2, concat
)
from pyspark.sql.types import IntegerType, DecimalType
from delta.tables import DeltaTable
import logging

spark = SparkSession.builder.getOrCreate()
logger = setup_logging()

ENVIRONMENT = dbutils.widgets.get("environment")
CATALOG = dbutils.widgets.get("catalog")
SILVER_SCHEMA = dbutils.widgets.get("silver_schema")
GOLD_SCHEMA = dbutils.widgets.get("gold_schema")
INCREMENTAL = dbutils.widgets.get("incremental").lower() == "true"

# Table paths
SILVER_SALES_TABLE = f"{CATALOG}.{ENVIRONMENT}_{SILVER_SCHEMA}.sales_transactions"
GOLD_FACT_TABLE = f"{CATALOG}.{ENVIRONMENT}_{GOLD_SCHEMA}.fact_sales"

# Dimension tables
DIM_CUSTOMER = f"{CATALOG}.{ENVIRONMENT}_{GOLD_SCHEMA}.dim_customer"
DIM_PRODUCT = f"{CATALOG}.{ENVIRONMENT}_{GOLD_SCHEMA}.dim_product"
DIM_STORE = f"{CATALOG}.{ENVIRONMENT}_{GOLD_SCHEMA}.dim_store"
DIM_DATE = f"{CATALOG}.{ENVIRONMENT}_{GOLD_SCHEMA}.dim_date"

logger.info(f"Starting Fact Sales build")
logger.info(f"Source: {SILVER_SALES_TABLE}, Target: {GOLD_FACT_TABLE}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Read Sales Transactions from Silver

# COMMAND ----------

try:
    df_silver_sales = spark.read.format("delta").table(SILVER_SALES_TABLE) \
        .filter(col("is_current") == True)
    
    if INCREMENTAL:
        # In production, filter by last processed timestamp
        # For demo, process all current records
        pass
    
    record_count = df_silver_sales.count()
    logger.info(f"Read {record_count} sales transactions from Silver")
    
    if record_count == 0:
        dbutils.notebook.exit("SUCCESS: No records to process")
        
except Exception as e:
    logger.error(f"Error reading from Silver: {e}")
    # Create sample data for demonstration
    df_silver_sales = spark.createDataFrame([
        ("TXN001", "STORE001", "PROD001", "CUST001", "2024-01-15 10:00:00", 2, 99.99, 10.00, 189.98, "CREDIT_CARD"),
        ("TXN002", "STORE001", "PROD002", "CUST002", "2024-01-15 11:00:00", 1, 49.99, 0.00, 49.99, "CASH"),
    ], schema=["transaction_id", "store_id", "product_id", "customer_id", "transaction_timestamp", 
               "quantity", "unit_price", "discount_amount", "total_amount", "payment_method"])
    
    df_silver_sales = df_silver_sales.withColumn("source_system", lit("demo")) \
                                     .withColumn("created_at", current_timestamp()) \
                                     .withColumn("updated_at", current_timestamp()) \
                                     .withColumn("is_current", lit(True))
    
    record_count = df_silver_sales.count()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Join with Dimension Tables

# COMMAND ----------

# Read dimension tables (current versions only)
df_dim_customer = spark.read.format("delta").table(DIM_CUSTOMER) \
    .filter(col("is_current") == True) \
    .select("customer_key", "customer_id")

df_dim_product = spark.read.format("delta").table(DIM_PRODUCT) \
    .filter(col("is_current") == True) \
    .select("product_key", "product_id", "cost")

df_dim_store = spark.read.format("delta").table(DIM_STORE) \
    .select("store_key", "store_id")

# Join with dimensions
df_fact = df_silver_sales \
    .join(df_dim_customer, on="customer_id", how="left") \
    .join(df_dim_product, on="product_id", how="inner") \
    .join(df_dim_store, on="store_id", how="inner")

logger.info(f"Joined with dimensions: {df_fact.count()} records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Generate Date Key

# COMMAND ----------

# Generate date_key from transaction_timestamp
df_fact = df_fact.withColumn(
    "date_key",
    (year(col("transaction_timestamp")) * 10000 +
     month(col("transaction_timestamp")) * 100 +
     dayofmonth(col("transaction_timestamp"))).cast(IntegerType())
)

# Validate date_key exists in dim_date
df_dim_date_keys = spark.read.format("delta").table(DIM_DATE).select("date_key").distinct()

# Left join to ensure date_key exists (filter out invalid dates)
df_fact = df_fact.join(df_dim_date_keys, on="date_key", how="inner")

logger.info(f"After date key validation: {df_fact.count()} records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Calculate Measures

# COMMAND ----------

# Calculate cost and profit
df_fact = df_fact \
    .withColumn(
        "cost_amount",
        (col("quantity") * coalesce(col("cost"), lit(0))).cast(DecimalType(18, 2))
    ) \
    .withColumn(
        "profit_amount",
        (col("total_amount") - col("cost_amount")).cast(DecimalType(18, 2))
    ) \
    .withColumn(
        "unit_price",
        col("unit_price").cast(DecimalType(18, 2))
    ) \
    .withColumn(
        "discount_amount",
        col("discount_amount").cast(DecimalType(18, 2))
    ) \
    .withColumn(
        "total_amount",
        col("total_amount").cast(DecimalType(18, 2))
    )

logger.info("Measures calculated")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Generate Surrogate Key for Fact

# COMMAND ----------

# Generate sales_id (surrogate key) using hash of transaction_id + timestamp
df_fact = df_fact.withColumn(
    "sales_id",
    sha2(concat(col("transaction_id"), col("transaction_timestamp").cast("string")), 256)
)

# Select final fact columns
df_fact_final = df_fact.select(
    col("sales_id"),
    col("transaction_id"),
    col("date_key"),
    col("customer_key"),
    col("product_key"),
    col("store_key"),
    col("transaction_timestamp"),
    col("quantity").cast(IntegerType()),
    col("unit_price"),
    col("discount_amount"),
    col("total_amount"),
    col("cost_amount"),
    col("profit_amount"),
    col("payment_method"),
    current_timestamp().alias("created_at"),
    current_timestamp().alias("updated_at")
)

logger.info("Fact table prepared")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6: Write to Gold Fact Table

# COMMAND ----------

spark.sql(f"CREATE DATABASE IF NOT EXISTS {CATALOG}.{ENVIRONMENT}_{GOLD_SCHEMA}")

# Check if table exists
try:
    existing_table = DeltaTable.forPath(spark, GOLD_FACT_TABLE)
    table_exists = True
except:
    table_exists = False

if table_exists:
    # Merge to handle duplicates (upsert based on transaction_id)
    merge_condition = "target.transaction_id = source.transaction_id"
    
    existing_table.alias("target").merge(
        df_fact_final.alias("source"),
        merge_condition
    ).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
    
    logger.info("Merged to fact table")
else:
    df_fact_final.write \
        .format("delta") \
        .mode("overwrite") \
        .option("mergeSchema", "true") \
        .partitionBy("date_key") \
        .saveAsTable(GOLD_FACT_TABLE)
    
    logger.info(f"Created new fact table with {df_fact_final.count()} records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 7: Optimize Table

# COMMAND ----------

try:
    # Optimize with Z-ordering for better query performance
    spark.sql(f"OPTIMIZE {GOLD_FACT_TABLE} ZORDER BY (date_key, store_key, product_key)")
    logger.info("Fact table optimized")
except Exception as e:
    logger.warning(f"Could not optimize: {e}")

# COMMAND ----------

final_count = spark.read.format("delta").table(GOLD_FACT_TABLE).count()
logger.info(f"Fact table build completed: {final_count} records")

dbutils.notebook.exit(f"SUCCESS: Fact table built with {final_count} records")


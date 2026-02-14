"""
Databricks Notebook: Silver to Gold - Dimension Store (SCD Type 1)
Builds Store dimension table with SCD Type 1 (overwrite changes).
"""

# MAGIC %md
# MAGIC # Silver to Gold: Dimension Store (SCD Type 1)
# MAGIC 
# MAGIC This notebook builds the Store dimension table using SCD Type 1 methodology:
# MAGIC - Overwrites attribute changes (no history maintained)
# MAGIC - Generates surrogate keys (store_key)
# MAGIC - Suitable for attributes where history is not needed

# COMMAND ----------

# MAGIC %run ../../utilities/common_functions
# MAGIC %run ../../utilities/schema_definitions

# COMMAND ----------

# Configuration
dbutils.widgets.text("environment", "dev", "Environment")
dbutils.widgets.text("catalog", "retail_datalake", "Unity Catalog")
dbutils.widgets.text("silver_schema", "silver", "Silver Schema Name")
dbutils.widgets.text("gold_schema", "gold", "Gold Schema Name")

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, current_timestamp, monotonically_increasing_id
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number
from pyspark.sql.types import IntegerType
from delta.tables import DeltaTable
import logging

spark = SparkSession.builder.getOrCreate()
logger = setup_logging()

ENVIRONMENT = dbutils.widgets.get("environment")
CATALOG = dbutils.widgets.get("catalog")
SILVER_SCHEMA = dbutils.widgets.get("silver_schema")
GOLD_SCHEMA = dbutils.widgets.get("gold_schema")

# For Store dimension, we'll derive it from orders/inventory in Silver
# In a real scenario, you might have a stores table in Silver
# For demonstration, creating from unique store_ids in orders

SILVER_ORDERS_TABLE = f"{CATALOG}.{ENVIRONMENT}_{SILVER_SCHEMA}.orders"
GOLD_TABLE = f"{CATALOG}.{ENVIRONMENT}_{GOLD_SCHEMA}.dim_store"

logger.info(f"Starting SCD Type 1 transformation for Store dimension")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Read Store Data from Silver

# COMMAND ----------

# Extract unique stores from orders (in real scenario, read from stores table)
df_silver_stores = spark.read.format("delta").table(SILVER_ORDERS_TABLE) \
    .select("store_id") \
    .distinct() \
    .filter(col("store_id").isNotNull())

# In production, you would read from a dedicated stores table:
# df_silver = spark.read.format("delta").table(f"{CATALOG}.{ENVIRONMENT}_{SILVER_SCHEMA}.stores")

# For demonstration, create store data
df_silver = df_silver_stores.withColumn("store_name", col("store_id")) \
                            .withColumn("store_type", lit("RETAIL")) \
                            .withColumn("address", lit(None)) \
                            .withColumn("city", lit(None)) \
                            .withColumn("state", lit(None)) \
                            .withColumn("zip_code", lit(None)) \
                            .withColumn("country", lit("USA")) \
                            .withColumn("phone", lit(None)) \
                            .withColumn("manager_name", lit(None)) \
                            .withColumn("opening_date", lit(None))

record_count = df_silver.count()
logger.info(f"Read {record_count} stores from Silver")

if record_count == 0:
    dbutils.notebook.exit("SUCCESS: No records to process")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Prepare Dimension Attributes (SCD Type 1)

# COMMAND ----------

spark.sql(f"CREATE DATABASE IF NOT EXISTS {CATALOG}.{ENVIRONMENT}_{GOLD_SCHEMA}")

# Check if table exists
try:
    df_gold_existing = spark.read.format("delta").table(GOLD_TABLE)
    table_exists = True
    max_key = df_gold_existing.agg({"store_key": "max"}).collect()[0][0]
    next_key = (max_key or 0) + 1
except:
    table_exists = False
    next_key = 1

# Generate surrogate keys
if table_exists:
    df_existing_keys = df_gold_existing.select("store_id", "store_key").distinct()
    df_silver_with_keys = df_silver.join(df_existing_keys, on="store_id", how="left")
    
    df_new_stores = df_silver_with_keys.filter(col("store_key").isNull())
    df_existing_stores = df_silver_with_keys.filter(col("store_key").isNotNull())
    
    if df_new_stores.count() > 0:
        window_spec = Window.orderBy("store_id")
        df_new_stores = df_new_stores.withColumn(
            "row_num",
            row_number().over(window_spec)
        ).withColumn(
            "store_key",
            (col("row_num") + next_key - 1).cast(IntegerType())
        ).drop("row_num")
        
        df_silver = df_existing_stores.union(df_new_stores)
else:
    window_spec = Window.orderBy("store_id")
    df_silver = df_silver.withColumn(
        "row_num",
        row_number().over(window_spec)
    ).withColumn(
        "store_key",
        (col("row_num") + next_key - 1).cast(IntegerType())
    ).drop("row_num")

# Prepare dimension
df_dim = df_silver.select(
    col("store_key"),
    col("store_id"),
    col("store_name"),
    col("store_type"),
    col("address"),
    col("city"),
    col("state"),
    col("zip_code"),
    col("country"),
    col("phone"),
    col("manager_name"),
    col("opening_date"),
    current_timestamp().alias("created_at"),
    current_timestamp().alias("updated_at")
)

logger.info("Dimension attributes prepared (SCD Type 1)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: SCD Type 1 Merge (Overwrite)

# COMMAND ----------

if table_exists:
    # SCD Type 1: Merge and update existing records (overwrite)
    delta_table = DeltaTable.forPath(spark, GOLD_TABLE)
    
    merge_condition = "target.store_id = source.store_id"
    
    delta_table.alias("target").merge(
        df_dim.alias("source"),
        merge_condition
    ).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
    
    logger.info("Merged records (SCD Type 1: overwrite)")
else:
    df_dim.write \
        .format("delta") \
        .mode("overwrite") \
        .option("mergeSchema", "true") \
        .saveAsTable(GOLD_TABLE)
    logger.info(f"Created new dimension table with {df_dim.count()} records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Optimize Table

# COMMAND ----------

try:
    spark.sql(f"OPTIMIZE {GOLD_TABLE}")
    logger.info("Table optimized")
except Exception as e:
    logger.warning(f"Could not optimize table: {e}")

# COMMAND ----------

final_count = spark.read.format("delta").table(GOLD_TABLE).count()
logger.info(f"Dimension build completed: {final_count} records")

dbutils.notebook.exit(f"SUCCESS: Dimension built with {final_count} records (SCD Type 1)")


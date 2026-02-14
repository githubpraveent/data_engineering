"""
Databricks Notebook: Silver to Gold - Dimension Product (SCD Type 2)
Builds Product dimension table with SCD Type 2 (historically accurate changes).
"""

# MAGIC %md
# MAGIC # Silver to Gold: Dimension Product (SCD Type 2)

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
from pyspark.sql.functions import (
    col, lit, current_timestamp, current_date, when, coalesce, max as spark_max
)
from pyspark.sql.types import IntegerType, DateType
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number
from delta.tables import DeltaTable
import logging

spark = SparkSession.builder.getOrCreate()
logger = setup_logging()

ENVIRONMENT = dbutils.widgets.get("environment")
CATALOG = dbutils.widgets.get("catalog")
SILVER_SCHEMA = dbutils.widgets.get("silver_schema")
GOLD_SCHEMA = dbutils.widgets.get("gold_schema")

# Read from products in Silver (create if not exists for demo)
SILVER_PRODUCTS_TABLE = f"{CATALOG}.{ENVIRONMENT}_{SILVER_SCHEMA}.products"
GOLD_TABLE = f"{CATALOG}.{ENVIRONMENT}_{GOLD_SCHEMA}.dim_product"

logger.info(f"Starting SCD Type 2 transformation for Product dimension")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Read from Silver

# COMMAND ----------

try:
    df_silver = spark.read.format("delta").table(SILVER_PRODUCTS_TABLE).filter(col("is_current") == True)
except:
    # Create sample products for demonstration
    df_silver = spark.createDataFrame([
        ("PROD001", "Product 1", "Electronics", "Smartphones", "Brand A", "Description 1", 99.99, 50.00, "SKU001"),
        ("PROD002", "Product 2", "Clothing", "Shirts", "Brand B", "Description 2", 49.99, 25.00, "SKU002"),
    ], schema=["product_id", "product_name", "category", "subcategory", "brand", "description", "unit_price", "cost", "sku"])
    
    df_silver = df_silver.withColumn("source_system", lit("demo")) \
                         .withColumn("created_at", current_timestamp()) \
                         .withColumn("updated_at", current_timestamp()) \
                         .withColumn("is_current", lit(True)) \
                         .withColumn("version", lit(1))

record_count = df_silver.count()
logger.info(f"Read {record_count} products from Silver")

if record_count == 0:
    dbutils.notebook.exit("SUCCESS: No records to process")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Generate Surrogate Keys

# COMMAND ----------

spark.sql(f"CREATE DATABASE IF NOT EXISTS {CATALOG}.{ENVIRONMENT}_{GOLD_SCHEMA}")

try:
    df_gold_existing = spark.read.format("delta").table(GOLD_TABLE)
    table_exists = True
    max_key = df_gold_existing.agg(spark_max("product_key")).collect()[0][0]
    next_key = (max_key or 0) + 1
except:
    table_exists = False
    next_key = 1

if table_exists:
    df_existing_keys = df_gold_existing.select("product_id", "product_key").distinct()
    df_silver_with_keys = df_silver.join(df_existing_keys, on="product_id", how="left")
    
    df_new_products = df_silver_with_keys.filter(col("product_key").isNull())
    df_existing_products = df_silver_with_keys.filter(col("product_key").isNotNull())
    
    if df_new_products.count() > 0:
        window_spec = Window.orderBy("product_id")
        df_new_products = df_new_products.withColumn(
            "row_num",
            row_number().over(window_spec)
        ).withColumn(
            "product_key",
            (col("row_num") + next_key - 1).cast(IntegerType())
        ).drop("row_num")
        
        df_silver = df_existing_products.union(df_new_products)
else:
    window_spec = Window.orderBy("product_id")
    df_silver = df_silver.withColumn(
        "row_num",
        row_number().over(window_spec)
    ).withColumn(
        "product_key",
        (col("row_num") + next_key - 1).cast(IntegerType())
    ).drop("row_num")

logger.info("Surrogate keys generated")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Prepare Dimension (SCD Type 2)

# COMMAND ----------

df_dim = df_silver.select(
    col("product_key"),
    col("product_id"),
    col("product_name"),
    col("category"),
    col("subcategory"),
    col("brand"),
    col("description"),
    col("unit_price"),
    col("cost"),
    col("sku"),
    current_date().alias("effective_date"),
    lit(None).cast(DateType()).alias("expiry_date"),
    lit(True).alias("is_current"),
    col("version"),
    current_timestamp().alias("created_at"),
    current_timestamp().alias("updated_at")
)

logger.info("Dimension attributes prepared (SCD Type 2)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: SCD Type 2 Merge

# COMMAND ----------

if table_exists:
    df_gold_current = spark.read.format("delta").table(GOLD_TABLE).filter(col("is_current") == True)
    
    df_changed = df_dim.join(
        df_gold_current.select(
            "product_key", "product_id", "product_name", "category", "subcategory",
            "brand", "description", "unit_price", "cost", "sku"
        ).alias("gold"),
        on="product_id",
        how="inner"
    ).filter(
        (col("product_name") != col("gold.product_name")) |
        (col("category") != col("gold.category")) |
        (col("subcategory") != col("gold.subcategory")) |
        (col("brand") != col("gold.brand")) |
        (col("unit_price") != col("gold.unit_price")) |
        (col("cost") != col("gold.cost")) |
        (col("sku") != col("gold.sku"))
    )
    
    df_new_products = df_dim.join(
        df_gold_current.select("product_id").alias("gold"),
        on="product_id",
        how="left_anti"
    )
    
    if df_changed.count() > 0:
        changed_product_ids = [row["product_id"] for row in df_changed.select("product_id").distinct().collect()]
        
        delta_table = DeltaTable.forPath(spark, GOLD_TABLE)
        delta_table.update(
            condition=(col("product_id").isin(changed_product_ids)) & (col("is_current") == True),
            set={
                "is_current": lit(False),
                "expiry_date": current_date() - lit(1),
                "updated_at": current_timestamp()
            }
        )
        
        logger.info(f"Expired {len(changed_product_ids)} old product records")
    
    df_to_insert = df_changed.select(df_dim.columns).union(df_new_products)
    
    if df_to_insert.count() > 0:
        df_to_insert.write.format("delta").mode("append").saveAsTable(GOLD_TABLE)
        logger.info(f"Inserted {df_to_insert.count()} new product records")
else:
    df_dim.write.format("delta").mode("overwrite").option("mergeSchema", "true").saveAsTable(GOLD_TABLE)
    logger.info(f"Created new dimension table with {df_dim.count()} records")

# COMMAND ----------

try:
    spark.sql(f"OPTIMIZE {GOLD_TABLE}")
except Exception as e:
    logger.warning(f"Could not optimize: {e}")

# COMMAND ----------

final_count = spark.read.format("delta").table(GOLD_TABLE).count()
current_count = spark.read.format("delta").table(GOLD_TABLE).filter(col("is_current") == True).count()

logger.info(f"Dimension build completed: {final_count} total, {current_count} current")

dbutils.notebook.exit(f"SUCCESS: Dimension built with {final_count} total, {current_count} current")


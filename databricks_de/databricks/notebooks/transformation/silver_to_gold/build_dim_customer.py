"""
Databricks Notebook: Silver to Gold - Dimension Customer (SCD Type 2)
Builds Customer dimension table with SCD Type 2 (historically accurate changes).
"""

# MAGIC %md
# MAGIC # Silver to Gold: Dimension Customer (SCD Type 2)
# MAGIC 
# MAGIC This notebook builds the Customer dimension table using SCD Type 2 methodology:
# MAGIC - Maintains full history of customer attribute changes
# MAGIC - Uses effective_date and expiry_date for time-based queries
# MAGIC - Generates surrogate keys (customer_key)
# MAGIC - Version tracking for each customer record

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
    col, lit, current_timestamp, current_date, when, coalesce, 
    min as spark_min, max as spark_max, datediff, date_add
)
from pyspark.sql.types import IntegerType, DateType
from delta.tables import DeltaTable
import logging

spark = SparkSession.builder.getOrCreate()
logger = setup_logging()

ENVIRONMENT = dbutils.widgets.get("environment")
CATALOG = dbutils.widgets.get("catalog")
SILVER_SCHEMA = dbutils.widgets.get("silver_schema")
GOLD_SCHEMA = dbutils.widgets.get("gold_schema")
INCREMENTAL = dbutils.widgets.get("incremental").lower() == "true"

SILVER_TABLE = f"{CATALOG}.{ENVIRONMENT}_{SILVER_SCHEMA}.customers"
GOLD_TABLE = f"{CATALOG}.{ENVIRONMENT}_{GOLD_SCHEMA}.dim_customer"

logger.info(f"Starting SCD Type 2 transformation for Customer dimension")
logger.info(f"Source: {SILVER_TABLE}, Target: {GOLD_TABLE}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Read from Silver Layer

# COMMAND ----------

df_silver = spark.read.format("delta").table(SILVER_TABLE).filter(col("is_current") == True)
record_count = df_silver.count()
logger.info(f"Read {record_count} current records from Silver")

if record_count == 0:
    dbutils.notebook.exit("SUCCESS: No records to process")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Read Existing Gold Dimension

# COMMAND ----------

# Create Gold schema if not exists
spark.sql(f"CREATE DATABASE IF NOT EXISTS {CATALOG}.{ENVIRONMENT}_{GOLD_SCHEMA}")

# Check if Gold table exists and read existing data
try:
    df_gold_existing = spark.read.format("delta").table(GOLD_TABLE)
    table_exists = True
    max_key = df_gold_existing.agg(spark_max("customer_key")).collect()[0][0]
    next_key = (max_key or 0) + 1
    logger.info(f"Existing Gold table found. Next customer_key: {next_key}")
except:
    table_exists = False
    next_key = 1
    logger.info("Creating new Gold dimension table")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Generate Surrogate Keys

# COMMAND ----------

from pyspark.sql.functions import monotonically_increasing_id, row_number
from pyspark.sql.window import Window

# Generate surrogate keys for new customers
if table_exists:
    # Get existing customer_keys to avoid conflicts
    df_existing_keys = df_gold_existing.select("customer_id", "customer_key").distinct()
    
    # Join with existing to preserve keys for existing customers
    df_silver_with_keys = df_silver.join(
        df_existing_keys,
        on="customer_id",
        how="left"
    )
    
    # Assign new keys to customers that don't have one
    df_new_customers = df_silver_with_keys.filter(col("customer_key").isNull())
    df_existing_customers = df_silver_with_keys.filter(col("customer_key").isNotNull())
    
    if df_new_customers.count() > 0:
        # Generate new keys starting from next_key
        window_spec = Window.orderBy("customer_id")
        df_new_customers = df_new_customers.withColumn(
            "row_num",
            row_number().over(window_spec)
        ).withColumn(
            "customer_key",
            (col("row_num") + next_key - 1).cast(IntegerType())
        ).drop("row_num")
        
        # Combine existing and new
        df_silver = df_existing_customers.union(df_new_customers)
else:
    # First time: assign keys sequentially
    window_spec = Window.orderBy("customer_id")
    df_silver = df_silver.withColumn(
        "row_num",
        row_number().over(window_spec)
    ).withColumn(
        "customer_key",
        (col("row_num") + next_key - 1).cast(IntegerType())
    ).drop("row_num")

logger.info("Surrogate keys generated")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Prepare Dimension Attributes

# COMMAND ----------

# Prepare dimension attributes with effective_date
df_dim = df_silver.select(
    col("customer_key"),
    col("customer_id"),
    col("first_name"),
    col("last_name"),
    col("full_name"),
    col("email"),
    col("phone"),
    col("address"),
    col("city"),
    col("state"),
    col("zip_code"),
    col("country"),
    col("date_of_birth"),
    col("registration_date"),
    current_date().alias("effective_date"),  # SCD Type 2: effective_date
    lit(None).cast(DateType()).alias("expiry_date"),  # Will be set on updates
    lit(True).alias("is_current"),  # SCD Type 2: is_current flag
    col("version"),
    current_timestamp().alias("created_at"),
    current_timestamp().alias("updated_at")
)

logger.info("Dimension attributes prepared")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: SCD Type 2 Merge Logic

# COMMAND ----------

if table_exists:
    # Perform SCD Type 2 merge
    from pyspark.sql.functions import struct
    
    # Read current records from Gold (only active ones)
    df_gold_current = spark.read.format("delta").table(GOLD_TABLE) \
        .filter(col("is_current") == True)
    
    # Join Silver and Gold to identify changes
    df_changed = df_dim.join(
        df_gold_current.select(
            "customer_key",
            "customer_id",
            "first_name", "last_name", "email", "phone",
            "address", "city", "state", "zip_code", "country",
            "date_of_birth", "registration_date"
        ).alias("gold"),
        on="customer_id",
        how="inner"
    ).filter(
        # Detect changes in any attribute
        (col("first_name") != col("gold.first_name")) |
        (col("last_name") != col("gold.last_name")) |
        (col("email") != col("gold.email")) |
        (col("phone") != col("gold.phone")) |
        (col("address") != col("gold.address")) |
        (col("city") != col("gold.city")) |
        (col("state") != col("gold.state")) |
        (col("zip_code") != col("gold.zip_code")) |
        (col("country") != col("gold.country")) |
        (col("date_of_birth") != col("gold.date_of_birth")) |
        (col("registration_date") != col("gold.registration_date"))
    )
    
    # Get new customers (not in Gold)
    df_new_customers = df_dim.join(
        df_gold_current.select("customer_id").alias("gold"),
        on="customer_id",
        how="left_anti"
    )
    
    # Update existing records: expire old versions
    if df_changed.count() > 0:
        changed_customer_ids = [row["customer_id"] for row in df_changed.select("customer_id").distinct().collect()]
        
        # Expire old records
        delta_table = DeltaTable.forPath(spark, GOLD_TABLE)
        delta_table.update(
            condition=(col("customer_id").isin(changed_customer_ids)) & (col("is_current") == True),
            set={
                "is_current": lit(False),
                "expiry_date": current_date() - lit(1),  # Set expiry to yesterday
                "updated_at": current_timestamp()
            }
        )
        
        logger.info(f"Expired {len(changed_customer_ids)} old customer records")
    
    # Insert new records (changed + new customers)
    df_to_insert = df_changed.select(df_dim.columns).union(df_new_customers)
    
    if df_to_insert.count() > 0:
        delta_table = DeltaTable.forPath(spark, GOLD_TABLE)
        df_to_insert.write.format("delta").mode("append").saveAsTable(GOLD_TABLE)
        logger.info(f"Inserted {df_to_insert.count()} new customer records")
else:
    # First load: insert all records
    df_dim.write \
        .format("delta") \
        .mode("overwrite") \
        .option("mergeSchema", "true") \
        .saveAsTable(GOLD_TABLE)
    logger.info(f"Created new dimension table with {df_dim.count()} records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6: Optimize Table

# COMMAND ----------

try:
    spark.sql(f"OPTIMIZE {GOLD_TABLE}")
    logger.info("Table optimized")
except Exception as e:
    logger.warning(f"Could not optimize table: {e}")

# COMMAND ----------

final_count = spark.read.format("delta").table(GOLD_TABLE).count()
current_count = spark.read.format("delta").table(GOLD_TABLE).filter(col("is_current") == True).count()

logger.info(f"Dimension build completed: {final_count} total records, {current_count} current records")

dbutils.notebook.exit(f"SUCCESS: Dimension built with {final_count} total records, {current_count} current")


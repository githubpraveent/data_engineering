"""
Databricks Notebook: Bronze to Silver - Customers
Transforms raw customers data from Bronze to cleaned Silver layer.
"""

# MAGIC %md
# MAGIC # Bronze to Silver Transformation: Customers

# COMMAND ----------

# MAGIC %run ../../utilities/common_functions
# MAGIC %run ../../utilities/schema_definitions

# COMMAND ----------

# Configuration
dbutils.widgets.text("environment", "dev", "Environment")
dbutils.widgets.text("catalog", "retail_datalake", "Unity Catalog")
dbutils.widgets.text("bronze_schema", "bronze", "Bronze Schema Name")
dbutils.widgets.text("silver_schema", "silver", "Silver Schema Name")
dbutils.widgets.text("incremental", "true", "Incremental Load")

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, lit, current_timestamp, trim, upper, concat, coalesce, when, to_date, lower
)
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number
from delta.tables import DeltaTable
import logging

spark = SparkSession.builder.getOrCreate()
logger = setup_logging()

ENVIRONMENT = dbutils.widgets.get("environment")
CATALOG = dbutils.widgets.get("catalog")
BRONZE_SCHEMA = dbutils.widgets.get("bronze_schema")
SILVER_SCHEMA = dbutils.widgets.get("silver_schema")
INCREMENTAL = dbutils.widgets.get("incremental").lower() == "true"

BRONZE_TABLE = f"{CATALOG}.{ENVIRONMENT}_{BRONZE_SCHEMA}.customers"
SILVER_TABLE = f"{CATALOG}.{ENVIRONMENT}_{SILVER_SCHEMA}.customers"

logger.info(f"Starting Bronze to Silver transformation for Customers")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Read from Bronze

# COMMAND ----------

df_bronze = spark.read.format("delta").table(BRONZE_TABLE)
record_count = df_bronze.count()
logger.info(f"Read {record_count} records from Bronze")

if record_count == 0:
    dbutils.notebook.exit("SUCCESS: No records to process")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Clean and Transform

# COMMAND ----------

df_silver = df_bronze \
    # Clean string fields
    .withColumn("customer_id", trim(col("customer_id"))) \
    .withColumn("first_name", trim(col("first_name"))) \
    .withColumn("last_name", trim(col("last_name"))) \
    .withColumn("email", lower(trim(col("email")))) \
    .withColumn("phone", trim(col("phone"))) \
    .withColumn("address", trim(col("address"))) \
    .withColumn("city", trim(col("city"))) \
    .withColumn("state", upper(trim(col("state")))) \
    .withColumn("zip_code", trim(col("zip_code"))) \
    .withColumn("country", upper(trim(col("country")))) \
    \
    # Create full_name
    .withColumn("full_name", 
                concat(
                    coalesce(col("first_name"), lit("")),
                    lit(" "),
                    coalesce(col("last_name"), lit(""))
                )) \
    \
    # Convert date columns
    .withColumn("date_of_birth", 
                coalesce(
                    to_date(col("date_of_birth"), "yyyy-MM-dd"),
                    to_date(col("date_of_birth"), "MM/dd/yyyy")
                )) \
    .withColumn("registration_date", 
                coalesce(
                    to_date(col("registration_date"), "yyyy-MM-dd"),
                    to_date(col("registration_date"), "MM/dd/yyyy")
                )) \
    \
    # Default country
    .withColumn("country", coalesce(col("country"), lit("USA"))) \
    \
    # Select columns
    .select(
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
        col("source_system"),
        current_timestamp().alias("created_at"),
        current_timestamp().alias("updated_at"),
        lit(True).alias("is_current"),
        lit(1).alias("version")
    )

logger.info("Data cleaning completed")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Validate

# COMMAND ----------

initial_count = df_silver.count()
df_silver = df_silver.filter(col("customer_id").isNotNull())
final_count = df_silver.count()

logger.info(f"Validation: {initial_count} → {final_count} records")

if final_count == 0:
    dbutils.notebook.exit("WARNING: No valid records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Deduplicate

# COMMAND ----------

window_spec = Window.partitionBy("customer_id").orderBy(col("created_at").desc())
df_silver = df_silver.withColumn("row_num", row_number().over(window_spec)) \
                     .filter(col("row_num") == 1) \
                     .drop("row_num")

dedup_count = df_silver.count()
logger.info(f"After deduplication: {dedup_count} records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Merge to Silver

# COMMAND ----------

spark.sql(f"CREATE DATABASE IF NOT EXISTS {CATALOG}.{ENVIRONMENT}_{SILVER_SCHEMA}")

try:
    silver_table = DeltaTable.forPath(spark, SILVER_TABLE)
    merge_condition = "target.customer_id = source.customer_id"
    silver_table.alias("target").merge(
        df_silver.alias("source"),
        merge_condition
    ).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
    logger.info("Merged to Silver table")
except:
    df_silver.write.format("delta").mode("overwrite").option("mergeSchema", "true").saveAsTable(SILVER_TABLE)
    logger.info(f"Created new Silver table: {SILVER_TABLE}")

# COMMAND ----------

try:
    spark.sql(f"ALTER TABLE {SILVER_TABLE} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")
    logger.info("CDF enabled")
except Exception as e:
    logger.warning(f"Could not enable CDF: {e}")

# COMMAND ----------

final_count = spark.read.format("delta").table(SILVER_TABLE).count()
logger.info(f"Transformation completed: {final_count} total records")

dbutils.notebook.exit(f"SUCCESS: {dedup_count} records processed, {final_count} total in Silver")


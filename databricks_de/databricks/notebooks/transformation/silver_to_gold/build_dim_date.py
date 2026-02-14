"""
Databricks Notebook: Silver to Gold - Dimension Date
Builds Date dimension table for time-based analytics.
"""

# MAGIC %md
# MAGIC # Silver to Gold: Dimension Date
# MAGIC 
# MAGIC This notebook builds a Date dimension table for time-based analytics.
# MAGIC Typically, this is a static dimension that covers a date range.

# COMMAND ----------

# MAGIC %run ../../utilities/common_functions
# MAGIC %run ../../utilities/schema_definitions

# COMMAND ----------

# Configuration
dbutils.widgets.text("environment", "dev", "Environment")
dbutils.widgets.text("catalog", "retail_datalake", "Unity Catalog")
dbutils.widgets.text("gold_schema", "gold", "Gold Schema Name")
dbutils.widgets.text("start_date", "2020-01-01", "Start Date")
dbutils.widgets.text("end_date", "2025-12-31", "End Date")

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, lit, to_date, year, month, dayofmonth, quarter, weekofyear,
    dayofweek, date_format, when, datediff
)
from pyspark.sql.types import IntegerType, DateType, BooleanType
import logging
from datetime import datetime, timedelta

spark = SparkSession.builder.getOrCreate()
logger = setup_logging()

ENVIRONMENT = dbutils.widgets.get("environment")
CATALOG = dbutils.widgets.get("catalog")
GOLD_SCHEMA = dbutils.widgets.get("gold_schema")
START_DATE = dbutils.widgets.get("start_date")
END_DATE = dbutils.widgets.get("end_date")

GOLD_TABLE = f"{CATALOG}.{ENVIRONMENT}_{GOLD_SCHEMA}.dim_date"

logger.info(f"Building Date dimension from {START_DATE} to {END_DATE}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Generate Date Range

# COMMAND ----------

spark.sql(f"CREATE DATABASE IF NOT EXISTS {CATALOG}.{ENVIRONMENT}_{GOLD_SCHEMA}")

# Generate date range
start = datetime.strptime(START_DATE, "%Y-%m-%d")
end = datetime.strptime(END_DATE, "%Y-%m-%d")

date_list = []
current_date = start
while current_date <= end:
    date_list.append(current_date.strftime("%Y-%m-%d"))
    current_date += timedelta(days=1)

# Create DataFrame
df_dates = spark.createDataFrame([(d,) for d in date_list], ["date_str"])

df_dates = df_dates.withColumn("date", to_date(col("date_str")))

logger.info(f"Generated {len(date_list)} dates")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Build Date Attributes

# COMMAND ----------

# Define US holidays (simplified - in production, use a proper holiday calendar)
us_holidays = [
    "2024-01-01", "2024-07-04", "2024-12-25",  # New Year, Independence, Christmas
    "2025-01-01", "2025-07-04", "2025-12-25",
]

df_dim_date = df_dates \
    .withColumn("date_key", (
        year(col("date")) * 10000 +
        month(col("date")) * 100 +
        dayofmonth(col("date"))
    ).cast(IntegerType())) \
    .withColumn("day", dayofmonth(col("date")).cast(IntegerType())) \
    .withColumn("month", month(col("date")).cast(IntegerType())) \
    .withColumn("year", year(col("date")).cast(IntegerType())) \
    .withColumn("quarter", quarter(col("date")).cast(IntegerType())) \
    .withColumn("week_of_year", weekofyear(col("date")).cast(IntegerType())) \
    .withColumn("day_of_week", dayofweek(col("date")).cast(IntegerType())) \
    .withColumn("day_name", date_format(col("date"), "EEEE")) \
    .withColumn("month_name", date_format(col("date"), "MMMM")) \
    .withColumn("is_weekend", when((dayofweek(col("date")) == 1) | (dayofweek(col("date")) == 7), True).otherwise(False)) \
    .withColumn("is_holiday", col("date_str").isin(us_holidays)) \
    .withColumn("holiday_name", 
                when(col("date_str") == "2024-01-01", "New Year's Day")
                .when(col("date_str") == "2024-07-04", "Independence Day")
                .when(col("date_str") == "2024-12-25", "Christmas Day")
                .when(col("date_str") == "2025-01-01", "New Year's Day")
                .when(col("date_str") == "2025-07-04", "Independence Day")
                .when(col("date_str") == "2025-12-25", "Christmas Day")
                .otherwise(None)) \
    .select(
        col("date_key"),
        col("date"),
        col("day"),
        col("month"),
        col("year"),
        col("quarter"),
        col("week_of_year"),
        col("day_of_week"),
        col("day_name"),
        col("month_name"),
        col("is_weekend"),
        col("is_holiday"),
        col("holiday_name")
    )

logger.info("Date attributes built")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Write to Gold Table

# COMMAND ----------

# Check if table exists
try:
    existing_count = spark.read.format("delta").table(GOLD_TABLE).count()
    if existing_count > 0:
        # Merge to update existing dates or add new ones
        from delta.tables import DeltaTable
        delta_table = DeltaTable.forPath(spark, GOLD_TABLE)
        delta_table.alias("target").merge(
            df_dim_date.alias("source"),
            "target.date_key = source.date_key"
        ).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
        logger.info("Merged date dimension")
    else:
        df_dim_date.write.format("delta").mode("overwrite").saveAsTable(GOLD_TABLE)
        logger.info("Created date dimension")
except:
    df_dim_date.write.format("delta").mode("overwrite").saveAsTable(GOLD_TABLE)
    logger.info("Created new date dimension table")

# COMMAND ----------

try:
    spark.sql(f"OPTIMIZE {GOLD_TABLE}")
except Exception as e:
    logger.warning(f"Could not optimize: {e}")

# COMMAND ----------

final_count = spark.read.format("delta").table(GOLD_TABLE).count()
logger.info(f"Date dimension built: {final_count} dates")

dbutils.notebook.exit(f"SUCCESS: Date dimension built with {final_count} dates")


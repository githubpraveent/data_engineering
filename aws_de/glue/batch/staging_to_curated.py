"""
AWS Glue Batch Job - Staging to Curated
Transforms cleaned staging data into business-ready curated format
Creates star schema dimensions and facts
"""
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import col, when, current_timestamp, lit, date_format, year, month, dayofmonth
from pyspark.sql.types import StringType

# Initialize Glue context
args = getResolvedOptions(sys.argv, [
    'JOB_NAME',
    's3_staging_path',
    's3_curated_path',
    'TempDir'
])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

s3_staging_path = args['s3_staging_path']
s3_curated_path = args['s3_curated_path']

# Read from staging zone
staging_df = spark.read.parquet(f"{s3_staging_path}*")

# Filter only valid records
valid_df = staging_df.filter(col("is_valid") == True)

# Create Dimension: Customer
customer_dim = valid_df.filter(col("table_name") == "customer") \
    .select(
        col("customer_id"),
        col("customer_name"),
        col("email"),
        col("phone"),
        col("address"),
        col("city"),
        col("state"),
        col("zip_code"),
        col("change_timestamp").alias("effective_date"),
        current_timestamp().alias("processed_at")
    ).distinct()

# Create Dimension: Date (from order dates)
order_df = valid_df.filter(col("table_name") == "order")
date_dim = order_df.select(
    date_format(col("order_date"), "yyyy-MM-dd").alias("date_key"),
    year(col("order_date")).alias("year"),
    month(col("order_date")).alias("month"),
    dayofmonth(col("order_date")).alias("day"),
    date_format(col("order_date"), "EEEE").alias("day_name"),
    date_format(col("order_date"), "MMMM").alias("month_name")
).distinct()

# Create Fact: Sales
sales_fact = order_df.filter(col("operation") != "d") \
    .select(
        col("order_id").alias("order_id"),
        col("customer_id"),
        date_format(col("order_date"), "yyyy-MM-dd").alias("order_date_key"),
        col("total_amount").alias("sales_amount"),
        col("status").alias("order_status"),
        col("change_timestamp").alias("transaction_timestamp"),
        current_timestamp().alias("processed_at")
    )

# Write curated data to S3
customer_dim.write \
    .mode("overwrite") \
    .partitionBy("state") \
    .parquet(f"{s3_curated_path}dimensions/customer/")

date_dim.write \
    .mode("overwrite") \
    .parquet(f"{s3_curated_path}dimensions/date/")

sales_fact.write \
    .mode("append") \
    .partitionBy("order_date_key") \
    .parquet(f"{s3_curated_path}facts/sales/")

job.commit()


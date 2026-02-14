"""
AWS Glue Batch Job - Landing to Staging
Transforms raw CDC events from landing zone to cleaned staging zone
Applies data quality checks, validation, and deduplication
"""
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import col, when, trim, upper, lower, regexp_replace, current_timestamp, lit, coalesce
from pyspark.sql.types import StringType

# Initialize Glue context
args = getResolvedOptions(sys.argv, [
    'JOB_NAME',
    's3_landing_path',
    's3_staging_path',
    'TempDir'
])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

s3_landing_path = args['s3_landing_path']
s3_staging_path = args['s3_staging_path']

# Read from landing zone (Parquet files)
landing_df = spark.read.parquet(f"{s3_landing_path}*")

# Data Quality and Validation Functions
def validate_and_clean_customer(df):
    """Validate and clean customer data"""
    cleaned_df = df.filter(col("table_name") == "customer")
    
    # Extract after_data for inserts/updates, before_data for deletes
    cleaned_df = cleaned_df.withColumn(
        "customer_id",
        coalesce(col("after_data.customer_id"), col("before_data.customer_id"))
    ).withColumn(
        "customer_name",
        coalesce(col("after_data.customer_name"), col("before_data.customer_name"))
    ).withColumn(
        "email",
        coalesce(col("after_data.email"), col("before_data.email"))
    ).withColumn(
        "phone",
        coalesce(col("after_data.phone"), col("before_data.phone"))
    ).withColumn(
        "address",
        coalesce(col("after_data.address"), col("before_data.address"))
    ).withColumn(
        "city",
        coalesce(col("after_data.city"), col("before_data.city"))
    ).withColumn(
        "state",
        coalesce(col("after_data.state"), col("before_data.state"))
    ).withColumn(
        "zip_code",
        coalesce(col("after_data.zip_code"), col("before_data.zip_code"))
    )
    
    # Data cleaning
    cleaned_df = cleaned_df.withColumn("customer_name", trim(col("customer_name"))) \
        .withColumn("email", lower(trim(col("email")))) \
        .withColumn("phone", regexp_replace(col("phone"), "[^0-9]", "")) \
        .withColumn("state", upper(trim(col("state")))) \
        .withColumn("zip_code", regexp_replace(col("zip_code"), "[^0-9]", ""))
    
    # Validation flags
    cleaned_df = cleaned_df.withColumn(
        "is_valid",
        when(
            col("customer_id").isNotNull() &
            col("customer_name").isNotNull() &
            col("email").isNotNull() &
            (col("email").rlike("^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$")),
            lit(True)
        ).otherwise(lit(False))
    )
    
    return cleaned_df

def validate_and_clean_order(df):
    """Validate and clean order data"""
    cleaned_df = df.filter(col("table_name") == "order")
    
    # Extract fields
    cleaned_df = cleaned_df.withColumn(
        "order_id",
        coalesce(col("after_data.order_id"), col("before_data.order_id"))
    ).withColumn(
        "customer_id",
        coalesce(col("after_data.customer_id"), col("before_data.customer_id"))
    ).withColumn(
        "order_date",
        coalesce(col("after_data.order_date"), col("before_data.order_date"))
    ).withColumn(
        "total_amount",
        coalesce(col("after_data.total_amount"), col("before_data.total_amount"))
    ).withColumn(
        "status",
        coalesce(col("after_data.status"), col("before_data.status"))
    )
    
    # Data cleaning
    cleaned_df = cleaned_df.withColumn("status", upper(trim(col("status"))))
    
    # Validation
    cleaned_df = cleaned_df.withColumn(
        "is_valid",
        when(
            col("order_id").isNotNull() &
            col("customer_id").isNotNull() &
            col("order_date").isNotNull() &
            col("total_amount").isNotNull() &
            (col("total_amount") >= 0),
            lit(True)
        ).otherwise(lit(False))
    )
    
    return cleaned_df

# Process each table type
customer_df = validate_and_clean_customer(landing_df)
order_df = validate_and_clean_order(landing_df)

# Combine all cleaned data
staging_df = customer_df.unionByName(order_df, allowMissingColumns=True)

# Add processing metadata
staging_df = staging_df.withColumn("processed_at", current_timestamp()) \
    .withColumn("processing_job", lit(args['JOB_NAME']))

# Deduplication based on key fields and timestamp
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number

window_spec = Window.partitionBy("table_name", "customer_id").orderBy(col("change_timestamp").desc())
deduplicated_df = staging_df.withColumn("row_num", row_number().over(window_spec)) \
    .filter(col("row_num") == 1) \
    .drop("row_num")

# Write to staging zone with partitioning
deduplicated_df.write \
    .mode("overwrite") \
    .partitionBy("table_name", "year", "month", "day") \
    .parquet(s3_staging_path)

job.commit()


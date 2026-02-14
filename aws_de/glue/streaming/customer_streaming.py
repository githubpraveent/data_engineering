"""
AWS Glue Streaming Job - Customer CDC from MSK to S3
Consumes customer CDC events from Kafka and writes to S3 landing zone
"""
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import col, from_json, current_timestamp, lit
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType

# Initialize Glue context
args = getResolvedOptions(sys.argv, [
    'JOB_NAME',
    'kafka.bootstrap.servers',
    'kafka.topic',
    's3_target_path',
    'TempDir'
])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Kafka connection parameters
kafka_bootstrap_servers = args['kafka.bootstrap.servers']
kafka_topic = args['kafka.topic']
s3_target_path = args['s3_target_path']

# Define schema for customer CDC events
customer_schema = StructType([
    StructField("op", StringType(), True),  # Operation: c, u, d (create, update, delete)
    StructField("ts_ms", TimestampType(), True),  # Timestamp
    StructField("before", StructType([
        StructField("customer_id", IntegerType(), True),
        StructField("customer_name", StringType(), True),
        StructField("email", StringType(), True),
        StructField("phone", StringType(), True),
        StructField("address", StringType(), True),
        StructField("city", StringType(), True),
        StructField("state", StringType(), True),
        StructField("zip_code", StringType(), True),
        StructField("created_at", TimestampType(), True),
        StructField("updated_at", TimestampType(), True)
    ]), True),
    StructField("after", StructType([
        StructField("customer_id", IntegerType(), True),
        StructField("customer_name", StringType(), True),
        StructField("email", StringType(), True),
        StructField("phone", StringType(), True),
        StructField("address", StringType(), True),
        StructField("city", StringType(), True),
        StructField("state", StringType(), True),
        StructField("zip_code", StringType(), True),
        StructField("created_at", TimestampType(), True),
        StructField("updated_at", TimestampType(), True)
    ]), True)
])

# Read from Kafka
kafka_df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
    .option("subscribe", kafka_topic) \
    .option("startingOffsets", "latest") \
    .option("kafka.security.protocol", "SASL_SSL") \
    .option("kafka.sasl.mechanism", "AWS_MSK_IAM") \
    .option("kafka.sasl.jaas.config", "software.amazon.msk.auth.iam.IAMLoginModule required;") \
    .option("kafka.sasl.client.callback.handler.class", "software.amazon.msk.auth.iam.IAMClientCallbackHandler") \
    .load()

# Parse Kafka messages
parsed_df = kafka_df.select(
    col("key").cast("string").alias("kafka_key"),
    from_json(col("value").cast("string"), customer_schema).alias("data"),
    col("timestamp").alias("kafka_timestamp"),
    col("partition"),
    col("offset")
)

# Extract and flatten customer data
customer_df = parsed_df.select(
    col("data.op").alias("operation"),
    col("data.ts_ms").alias("change_timestamp"),
    col("data.before").alias("before_data"),
    col("data.after").alias("after_data"),
    col("kafka_timestamp"),
    col("partition"),
    col("offset"),
    current_timestamp().alias("ingestion_timestamp")
)

# Add metadata
enriched_df = customer_df.withColumn("table_name", lit("customer")) \
    .withColumn("source_system", lit("azure_sql_server")) \
    .withColumn("environment", lit("dev"))  # Should be parameterized

# Write to S3 in Parquet format with partitioning
def write_to_s3(batch_df, batch_id):
    batch_df.write \
        .mode("append") \
        .partitionBy("table_name", "year", "month", "day", "hour") \
        .parquet(s3_target_path)

# Add partition columns
partitioned_df = enriched_df \
    .withColumn("year", col("ingestion_timestamp").substr(1, 4)) \
    .withColumn("month", col("ingestion_timestamp").substr(6, 2)) \
    .withColumn("day", col("ingestion_timestamp").substr(9, 2)) \
    .withColumn("hour", col("ingestion_timestamp").substr(12, 2))

# Write stream to S3
query = partitioned_df.writeStream \
    .format("parquet") \
    .outputMode("append") \
    .option("path", s3_target_path) \
    .option("checkpointLocation", f"{args['TempDir']}/checkpoints/customer") \
    .partitionBy("table_name", "year", "month", "day", "hour") \
    .trigger(processingTime='60 seconds') \
    .start()

query.awaitTermination()

job.commit()


"""
Test cases for Bronze layer ingestion.
"""

import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, DoubleType
from pyspark.sql.functions import col


@pytest.fixture
def spark():
    """Create Spark session for testing."""
    return SparkSession.builder \
        .appName("BronzeLayerTests") \
        .master("local[2]") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .getOrCreate()


@pytest.fixture
def sample_bronze_data(spark):
    """Create sample Bronze data for testing."""
    schema = StructType([
        StructField("event_id", StringType(), False),
        StructField("customer_id", StringType(), False),
        StructField("event_type", StringType(), False),
        StructField("timestamp", TimestampType(), False),
        StructField("amount", DoubleType(), True)
    ])
    
    data = [
        ("evt_001", "cust_001", "PURCHASE", "2024-01-01 10:00:00", 99.99),
        ("evt_002", "cust_002", "CLICK", "2024-01-01 10:05:00", None),
        ("evt_003", "cust_001", "REVIEW", "2024-01-01 10:10:00", None)
    ]
    
    return spark.createDataFrame(data, schema)


def test_bronze_schema_validation(spark, sample_bronze_data):
    """Test that Bronze data has correct schema."""
    assert sample_bronze_data.schema is not None
    assert "event_id" in sample_bronze_data.columns
    assert "customer_id" in sample_bronze_data.columns
    assert "event_type" in sample_bronze_data.columns


def test_bronze_data_quality(sample_bronze_data):
    """Test data quality checks on Bronze data."""
    # Check for null event_ids (should not exist)
    null_event_ids = sample_bronze_data.filter(col("event_id").isNull()).count()
    assert null_event_ids == 0, "Event IDs should not be null"
    
    # Check for null customer_ids (should not exist)
    null_customer_ids = sample_bronze_data.filter(col("customer_id").isNull()).count()
    assert null_customer_ids == 0, "Customer IDs should not be null"


def test_bronze_timestamp_format(sample_bronze_data):
    """Test that timestamps are in correct format."""
    # All timestamps should be non-null
    null_timestamps = sample_bronze_data.filter(col("timestamp").isNull()).count()
    assert null_timestamps == 0, "Timestamps should not be null"


def test_bronze_event_types(sample_bronze_data):
    """Test that event types are valid."""
    valid_event_types = ["PURCHASE", "CLICK", "REVIEW", "PAGE_VIEW"]
    invalid_events = sample_bronze_data.filter(
        ~col("event_type").isin(valid_event_types)
    ).count()
    assert invalid_events == 0, "All event types should be valid"

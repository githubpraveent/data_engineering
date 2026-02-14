"""
Test cases for Silver layer transformations.
"""

import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, DoubleType, BooleanType
from pyspark.sql.functions import col


@pytest.fixture
def spark():
    """Create Spark session for testing."""
    return SparkSession.builder \
        .appName("SilverLayerTests") \
        .master("local[2]") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .getOrCreate()


@pytest.fixture
def sample_silver_data(spark):
    """Create sample Silver data for testing."""
    schema = StructType([
        StructField("event_id", StringType(), False),
        StructField("customer_id", StringType(), False),
        StructField("event_type", StringType(), False),
        StructField("timestamp", TimestampType(), False),
        StructField("amount", DoubleType(), True),
        StructField("quality_score", DoubleType(), True),
        StructField("is_high_quality", BooleanType(), True),
        StructField("is_purchase", BooleanType(), True)
    ])
    
    data = [
        ("evt_001", "cust_001", "PURCHASE", "2024-01-01 10:00:00", 99.99, 0.95, True, True),
        ("evt_002", "cust_002", "CLICK", "2024-01-01 10:05:00", None, 0.85, True, False),
        ("evt_003", "cust_001", "REVIEW", "2024-01-01 10:10:00", None, 0.90, True, False)
    ]
    
    return spark.createDataFrame(data, schema)


def test_silver_quality_scores(sample_silver_data):
    """Test that quality scores are within valid range."""
    invalid_scores = sample_silver_data.filter(
        (col("quality_score") < 0) | (col("quality_score") > 1)
    ).count()
    assert invalid_scores == 0, "Quality scores should be between 0 and 1"


def test_silver_deduplication(sample_silver_data):
    """Test that duplicate event_ids are removed."""
    duplicate_count = (
        sample_silver_data
        .groupBy("event_id")
        .count()
        .filter(col("count") > 1)
        .count()
    )
    assert duplicate_count == 0, "No duplicate event_ids should exist"


def test_silver_purchase_flag(sample_silver_data):
    """Test that purchase flag is correctly set."""
    purchases = sample_silver_data.filter(
        (col("is_purchase") == True) & (col("event_type") != "PURCHASE")
    ).count()
    assert purchases == 0, "is_purchase should only be True for PURCHASE events"


def test_silver_amount_validation(sample_silver_data):
    """Test that amounts are non-negative."""
    negative_amounts = sample_silver_data.filter(
        (col("amount").isNotNull()) & (col("amount") < 0)
    ).count()
    assert negative_amounts == 0, "Amounts should not be negative"

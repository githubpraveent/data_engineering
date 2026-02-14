"""
Test cases for Gold layer aggregations.
"""

import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DateType, DoubleType, LongType
from pyspark.sql.functions import col


@pytest.fixture
def spark():
    """Create Spark session for testing."""
    return SparkSession.builder \
        .appName("GoldLayerTests") \
        .master("local[2]") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .getOrCreate()


@pytest.fixture
def sample_gold_data(spark):
    """Create sample Gold data for testing."""
    schema = StructType([
        StructField("customer_id", StringType(), False),
        StructField("event_date", DateType(), False),
        StructField("total_events", LongType(), True),
        StructField("total_purchases", LongType(), True),
        StructField("total_revenue", DoubleType(), True),
        StructField("conversion_rate", DoubleType(), True)
    ])
    
    data = [
        ("cust_001", "2024-01-01", 10, 2, 199.98, 0.2),
        ("cust_002", "2024-01-01", 5, 1, 99.99, 0.2),
        ("cust_001", "2024-01-02", 8, 3, 299.97, 0.375)
    ]
    
    return spark.createDataFrame(data, schema)


def test_gold_aggregation_consistency(sample_gold_data):
    """Test that aggregations are mathematically consistent."""
    # Conversion rate should equal purchases / events
    inconsistent = sample_gold_data.filter(
        (col("total_events") > 0) &
        (abs(col("conversion_rate") - (col("total_purchases") / col("total_events"))) > 0.001)
    ).count()
    assert inconsistent == 0, "Conversion rate should equal purchases/events"


def test_gold_revenue_consistency(sample_gold_data):
    """Test that revenue is non-negative."""
    negative_revenue = sample_gold_data.filter(col("total_revenue") < 0).count()
    assert negative_revenue == 0, "Revenue should not be negative"


def test_gold_conversion_rate_range(sample_gold_data):
    """Test that conversion rates are between 0 and 1."""
    invalid_rates = sample_gold_data.filter(
        (col("conversion_rate") < 0) | (col("conversion_rate") > 1)
    ).count()
    assert invalid_rates == 0, "Conversion rates should be between 0 and 1"


def test_gold_purchases_less_than_events(sample_gold_data):
    """Test that purchases are never more than total events."""
    invalid = sample_gold_data.filter(
        col("total_purchases") > col("total_events")
    ).count()
    assert invalid == 0, "Purchases should not exceed total events"

"""
Unit tests for Databricks transformation notebooks.
"""

import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DecimalType, DateType, TimestampType
from pyspark.sql.functions import col, lit, current_timestamp
from databricks.notebooks.utilities.schema_definitions import (
    BRONZE_ORDERS_SCHEMA, SILVER_ORDERS_SCHEMA,
    BRONZE_CUSTOMERS_SCHEMA, SILVER_CUSTOMERS_SCHEMA
)
from databricks.notebooks.utilities.data_quality_checks import (
    check_not_null, check_unique, check_value_range,
    check_row_count, run_quality_checks
)


@pytest.fixture(scope="session")
def spark():
    """Create Spark session for testing."""
    return SparkSession.builder \
        .master("local[2]") \
        .appName("test") \
        .getOrCreate()


@pytest.fixture
def sample_orders_data(spark):
    """Create sample orders data for testing."""
    data = [
        ("ORD001", "CUST001", "2024-01-15", "COMPLETED", "150.00", "USD", "STORE001", "CREDIT_CARD"),
        ("ORD002", "CUST002", "2024-01-16", "PENDING", "75.50", "USD", "STORE002", "CASH"),
    ]
    return spark.createDataFrame(data, schema=BRONZE_ORDERS_SCHEMA)


@pytest.fixture
def sample_customers_data(spark):
    """Create sample customers data for testing."""
    data = [
        ("CUST001", "John", "Doe", "john.doe@email.com", "555-0101", "123 Main St", "New York", "NY", "10001", "USA", "1980-05-15", "2020-01-01"),
        ("CUST002", "Jane", "Smith", "jane.smith@email.com", "555-0102", "456 Oak Ave", "Los Angeles", "CA", "90001", "USA", "1985-08-20", "2020-02-15"),
    ]
    return spark.createDataFrame(data, schema=BRONZE_CUSTOMERS_SCHEMA)


def test_check_not_null_pass(spark, sample_orders_data):
    """Test not null check passes."""
    passed, null_count = check_not_null(sample_orders_data, "order_id")
    assert passed is True
    assert null_count == 0


def test_check_not_null_fail(spark):
    """Test not null check fails."""
    data = spark.createDataFrame([
        ("ORD001", None),
        ("ORD002", "CUST002"),
    ], schema=["order_id", "customer_id"])
    
    passed, null_count = check_not_null(data, "customer_id")
    assert passed is False
    assert null_count > 0


def test_check_unique_pass(spark, sample_orders_data):
    """Test unique check passes."""
    passed, duplicate_count = check_unique(sample_orders_data, "order_id")
    assert passed is True
    assert duplicate_count == 0


def test_check_unique_fail(spark):
    """Test unique check fails."""
    data = spark.createDataFrame([
        ("ORD001", "CUST001"),
        ("ORD001", "CUST002"),
    ], schema=["order_id", "customer_id"])
    
    passed, duplicate_count = check_unique(data, "order_id")
    assert passed is False
    assert duplicate_count > 0


def test_check_value_range_pass(spark):
    """Test value range check passes."""
    data = spark.createDataFrame([
        (100.00,),
        (200.00,),
        (150.00,),
    ], schema=["total_amount"])
    
    passed, violations = check_value_range(data, "total_amount", min_value=0.0, max_value=1000.0)
    assert passed is True
    assert violations == 0


def test_check_value_range_fail(spark):
    """Test value range check fails."""
    data = spark.createDataFrame([
        (-100.00,),
        (200.00,),
        (1500.00,),
    ], schema=["total_amount"])
    
    passed, violations = check_value_range(data, "total_amount", min_value=0.0, max_value=1000.0)
    assert passed is False
    assert violations > 0


def test_check_row_count(spark, sample_orders_data):
    """Test row count check."""
    passed, count = check_row_count(sample_orders_data, min_rows=1, max_rows=10)
    assert passed is True
    assert count == 2


def test_run_quality_checks(spark, sample_orders_data):
    """Test running multiple quality checks."""
    checks = {
        "not_null_order_id": {
            "type": "not_null",
            "column": "order_id"
        },
        "unique_order_id": {
            "type": "unique",
            "column": "order_id"
        }
    }
    
    results = run_quality_checks(sample_orders_data, checks)
    
    assert "not_null_order_id" in results
    assert "unique_order_id" in results
    assert results["not_null_order_id"]["passed"] is True
    assert results["unique_order_id"]["passed"] is True


def test_schema_validation(spark, sample_orders_data):
    """Test schema validation."""
    # Check that DataFrame matches expected schema
    assert sample_orders_data.schema == BRONZE_ORDERS_SCHEMA
    assert "order_id" in sample_orders_data.columns
    assert "customer_id" in sample_orders_data.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


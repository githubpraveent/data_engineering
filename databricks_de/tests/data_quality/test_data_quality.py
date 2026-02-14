"""
Data quality tests for retail data lakehouse.
"""

import pytest
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, current_timestamp
from databricks.notebooks.utilities.data_quality_checks import (
    check_not_null, check_unique, check_referential_integrity,
    check_row_count, validate_all_checks_passed, run_quality_checks
)


@pytest.fixture(scope="session")
def spark():
    """Create Spark session for testing."""
    return SparkSession.builder \
        .master("local[2]") \
        .appName("data-quality-test") \
        .getOrCreate()


def test_silver_orders_quality(spark):
    """Test data quality for Silver orders table."""
    # In production, read from actual Silver table
    # For testing, create sample data
    df_silver_orders = spark.createDataFrame([
        ("ORD001", "CUST001", "2024-01-15", "COMPLETED", 150.00, "USD", "STORE001"),
        ("ORD002", "CUST002", "2024-01-16", "PENDING", 75.50, "USD", "STORE002"),
    ], schema=["order_id", "customer_id", "order_date", "order_status", "total_amount", "currency", "store_id"])
    
    # Run quality checks
    checks = {
        "not_null_order_id": {"type": "not_null", "column": "order_id"},
        "not_null_total_amount": {"type": "not_null", "column": "total_amount"},
        "unique_order_id": {"type": "unique", "column": "order_id"},
        "value_range_total_amount": {"type": "value_range", "column": "total_amount", "min": 0.0, "max": 1000000.0},
    }
    
    results = run_quality_checks(df_silver_orders, checks)
    
    assert validate_all_checks_passed(results)


def test_silver_customers_quality(spark):
    """Test data quality for Silver customers table."""
    df_silver_customers = spark.createDataFrame([
        ("CUST001", "John", "Doe", "john.doe@email.com"),
        ("CUST002", "Jane", "Smith", "jane.smith@email.com"),
    ], schema=["customer_id", "first_name", "last_name", "email"])
    
    checks = {
        "not_null_customer_id": {"type": "not_null", "column": "customer_id"},
        "unique_customer_id": {"type": "unique", "column": "customer_id"},
    }
    
    results = run_quality_checks(df_silver_customers, checks)
    
    assert validate_all_checks_passed(results)


def test_gold_fact_sales_referential_integrity(spark):
    """Test referential integrity between fact and dimension tables."""
    # Create sample fact table
    df_fact_sales = spark.createDataFrame([
        (1, "TXN001", 1, 100, 1, 1),
        (2, "TXN002", 1, 200, 2, 1),
    ], schema=["sales_id", "transaction_id", "date_key", "customer_key", "product_key", "store_key"])
    
    # Create sample dimension tables
    df_dim_customer = spark.createDataFrame([
        (1, "CUST001"),
        (2, "CUST002"),
    ], schema=["customer_key", "customer_id"])
    
    df_dim_product = spark.createDataFrame([
        (1, "PROD001"),
        (2, "PROD002"),
    ], schema=["product_key", "product_id"])
    
    df_dim_store = spark.createDataFrame([
        (1, "STORE001"),
    ], schema=["store_key", "store_id"])
    
    # Check referential integrity
    passed_customer, orphan_count_customer = check_referential_integrity(
        df_fact_sales, df_dim_customer, "customer_key", "customer_key"
    )
    
    passed_product, orphan_count_product = check_referential_integrity(
        df_fact_sales, df_dim_product, "product_key", "product_key"
    )
    
    passed_store, orphan_count_store = check_referential_integrity(
        df_fact_sales, df_dim_store, "store_key", "store_key"
    )
    
    assert passed_customer is True
    assert passed_product is True
    assert passed_store is True
    assert orphan_count_customer == 0
    assert orphan_count_product == 0
    assert orphan_count_store == 0


def test_gold_fact_sales_row_count(spark):
    """Test row count for Gold fact sales table."""
    df_fact_sales = spark.createDataFrame([
        (1, "TXN001", 20240115, 1, 100, 1, 1),
    ], schema=["sales_id", "transaction_id", "date_key", "customer_key", "product_key", "store_key", "quantity"])
    
    passed, count = check_row_count(df_fact_sales, min_rows=1, max_rows=1000000)
    
    assert passed is True
    assert count >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


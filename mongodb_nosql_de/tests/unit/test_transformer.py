"""
Unit tests for DataTransformer
"""

import pytest
from datetime import datetime
from transform.transformer import DataTransformer
from config.settings import Settings


def test_transform_record(test_settings, sample_transaction_data):
    """Test record transformation"""
    transformer = DataTransformer(test_settings)
    
    transformed = transformer._transform_record(sample_transaction_data[0], 0)
    
    assert transformed["transaction_id"] == "TXN001"
    assert transformed["product_id"] == "PROD001"
    assert transformed["quantity"] == 2.0
    assert transformed["unit_price"] == 29.99
    assert transformed["total_amount"] == 59.98
    assert "timestamp" in transformed
    assert isinstance(transformed["timestamp"], datetime)


def test_parse_timestamp():
    """Test timestamp parsing"""
    transformer = DataTransformer(Settings(environment="test", mongodb_uri="mongodb://localhost/test"))
    
    # Test various formats
    assert isinstance(transformer._parse_timestamp("2024-01-15 10:30:00"), datetime)
    assert isinstance(transformer._parse_timestamp("2024-01-15"), datetime)
    assert isinstance(transformer._parse_timestamp(datetime.now()), datetime)


def test_parse_numeric():
    """Test numeric parsing"""
    transformer = DataTransformer(Settings(environment="test", mongodb_uri="mongodb://localhost/test"))
    
    assert transformer._parse_numeric("29.99") == 29.99
    assert transformer._parse_numeric("$29.99") == 29.99
    assert transformer._parse_numeric("1,234.56") == 1234.56
    assert transformer._parse_numeric(42) == 42.0
    assert transformer._parse_numeric(3.14) == 3.14


def test_transform_batch(test_settings, sample_transaction_data):
    """Test batch transformation"""
    transformer = DataTransformer(test_settings)
    
    transformed = transformer.transform(sample_transaction_data)
    
    assert len(transformed) == 2
    assert all("_id" in record for record in transformed)
    assert all("timestamp" in record for record in transformed)

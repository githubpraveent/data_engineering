"""
Unit tests for DataQualityValidator
"""

import pytest
from quality.validator import DataQualityValidator
from config.settings import Settings


def test_validate_schema(test_settings):
    """Test schema validation"""
    validator = DataQualityValidator(test_settings)
    
    data = [
        {
            "_id": "1",
            "transaction_id": "TXN001",
            "timestamp": "2024-01-15",
            "product_id": "PROD001",
            "total_amount": 59.98
        },
        {
            "_id": "2",
            "transaction_id": "TXN002",
            # Missing required fields
        }
    ]
    
    result = validator._validate_schema(data)
    
    assert result["total"] == 8  # 2 records * 4 required fields
    assert result["passed"] < result["total"]  # Some fields missing
    assert len(result["invalid_records"]) > 0


def test_validate_completeness(test_settings):
    """Test completeness validation"""
    validator = DataQualityValidator(test_settings)
    
    data = [
        {"_id": "1", "field1": "value1", "field2": "value2", "field3": None},
        {"_id": "2", "field1": "value1", "field2": None, "field3": None}
    ]
    
    result = validator._validate_completeness(data)
    
    assert result["total"] == 2
    assert result["passed"] >= 0


def test_validate_accuracy(test_settings):
    """Test accuracy validation"""
    validator = DataQualityValidator(test_settings)
    
    data = [
        {
            "_id": "1",
            "quantity": 2,
            "unit_price": 29.99,
            "total_amount": 59.98
        },
        {
            "_id": "2",
            "quantity": -1,  # Invalid negative
            "unit_price": 29.99,
            "total_amount": -29.99  # Invalid
        }
    ]
    
    result = validator._validate_accuracy(data)
    
    assert result["passed"] < result["total"]  # Some invalid records
    assert len(result["invalid_records"]) > 0


def test_validate_uniqueness(test_settings):
    """Test uniqueness validation"""
    validator = DataQualityValidator(test_settings)
    
    data = [
        {"_id": "1", "transaction_id": "TXN001"},
        {"_id": "2", "transaction_id": "TXN002"},
        {"_id": "3", "transaction_id": "TXN001"}  # Duplicate
    ]
    
    result = validator._validate_uniqueness(data)
    
    assert len(result["invalid_records"]) > 0  # Duplicate found


def test_full_validation(test_settings):
    """Test full validation process"""
    validator = DataQualityValidator(test_settings)
    
    data = [
        {
            "_id": "1",
            "transaction_id": "TXN001",
            "timestamp": "2024-01-15",
            "product_id": "PROD001",
            "quantity": 2,
            "unit_price": 29.99,
            "total_amount": 59.98
        }
    ]
    
    result = validator.validate(data)
    
    assert isinstance(result.passed, bool)
    assert 0.0 <= result.quality_score <= 1.0

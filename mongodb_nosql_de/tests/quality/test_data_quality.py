"""
Data quality validation tests
"""

import pytest
from quality.validator import DataQualityValidator, ValidationResult
from config.settings import Settings


def test_data_quality_thresholds():
    """Test data quality threshold validation"""
    settings = Settings(
        environment="test",
        mongodb_uri="mongodb://localhost/test",
        dq_completeness_threshold=0.95,
        dq_accuracy_threshold=0.90,
        dq_uniqueness_threshold=0.99
    )
    
    validator = DataQualityValidator(settings)
    
    # High quality data
    good_data = [
        {
            "_id": f"TXN{i:03d}",
            "transaction_id": f"TXN{i:03d}",
            "timestamp": "2024-01-15",
            "product_id": f"PROD{i:03d}",
            "quantity": 1,
            "unit_price": 10.0,
            "total_amount": 10.0
        }
        for i in range(100)
    ]
    
    result = validator.validate(good_data)
    
    assert result.quality_score >= 0.95
    assert result.passed is True


def test_low_quality_data_rejection():
    """Test that low quality data is properly flagged"""
    settings = Settings(
        environment="test",
        mongodb_uri="mongodb://localhost/test",
        dq_strict_mode=True,
        dq_completeness_threshold=0.95
    )
    
    validator = DataQualityValidator(settings)
    
    # Poor quality data with many missing fields
    bad_data = [
        {
            "_id": f"TXN{i:03d}",
            "transaction_id": f"TXN{i:03d}",
            # Missing required fields
        }
        for i in range(50)
    ]
    
    result = validator.validate(bad_data)
    
    assert result.quality_score < 0.95
    assert result.passed is False
    assert len(result.invalid_records) > 0

"""
Unit tests for DataExtractor
"""

import pytest
from pathlib import Path
from extract.extractor import DataExtractor
from config.settings import Settings


def test_extract_csv(test_settings, tmp_path):
    """Test CSV extraction"""
    # Create test CSV file
    test_csv = tmp_path / "test.csv"
    test_csv.write_text(
        "transaction_id,product_id,quantity,unit_price\n"
        "TXN001,PROD001,2,29.99\n"
        "TXN002,PROD002,1,49.99\n"
    )
    
    test_settings.source_path = str(test_csv)
    extractor = DataExtractor(test_settings)
    
    data = extractor.extract()
    
    assert len(data) == 2
    assert data[0]["transaction_id"] == "TXN001"
    assert data[1]["product_id"] == "PROD002"


def test_extract_json(test_settings, tmp_path):
    """Test JSON extraction"""
    import json
    
    # Create test JSON file
    test_json = tmp_path / "test.json"
    test_data = [
        {"transaction_id": "TXN001", "product_id": "PROD001"},
        {"transaction_id": "TXN002", "product_id": "PROD002"}
    ]
    test_json.write_text(json.dumps(test_data))
    
    test_settings.source_type = "json"
    test_settings.source_path = str(test_json)
    extractor = DataExtractor(test_settings)
    
    data = extractor.extract()
    
    assert len(data) == 2
    assert data[0]["transaction_id"] == "TXN001"


def test_extract_csv_not_found(test_settings):
    """Test extraction when file not found"""
    test_settings.source_path = "/nonexistent/file.csv"
    extractor = DataExtractor(test_settings)
    
    with pytest.raises(FileNotFoundError):
        extractor.extract()

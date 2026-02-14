"""
Pytest configuration and fixtures
"""

import pytest
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config.settings import Settings


@pytest.fixture
def test_settings():
    """Create test settings"""
    return Settings(
        environment="test",
        mongodb_uri="mongodb://localhost:27017/test_db",
        mongodb_database="test_db",
        source_type="csv",
        source_path=str(Path(__file__).parent.parent / "data" / "sample" / "transactions_sample.csv"),
        batch_size=10,
        dq_enabled=True,
        dq_strict_mode=False
    )


@pytest.fixture
def sample_transaction_data():
    """Sample transaction data for testing"""
    return [
        {
            "transaction_id": "TXN001",
            "timestamp": "2024-01-15 10:30:00",
            "product_id": "PROD001",
            "customer_id": "CUST001",
            "quantity": 2,
            "unit_price": 29.99,
            "total_amount": 59.98,
            "currency": "USD",
            "payment_method": "credit_card",
            "region": "North America",
            "category": "Electronics"
        },
        {
            "transaction_id": "TXN002",
            "timestamp": "2024-01-15 11:15:00",
            "product_id": "PROD002",
            "customer_id": "CUST002",
            "quantity": 1,
            "unit_price": 49.99,
            "total_amount": 49.99,
            "currency": "USD",
            "payment_method": "debit_card",
            "region": "North America",
            "category": "Clothing"
        }
    ]


@pytest.fixture
def mock_mongodb_client(monkeypatch):
    """Mock MongoDB client"""
    from unittest.mock import MagicMock
    
    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_collection = MagicMock()
    
    mock_client.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_collection
    
    return mock_client, mock_db, mock_collection

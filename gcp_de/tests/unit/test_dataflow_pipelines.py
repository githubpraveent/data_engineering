"""
Unit tests for Dataflow pipelines.
"""

import unittest
from unittest.mock import Mock, patch
import json
from datetime import datetime

# Import pipeline modules
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../dataflow'))

from streaming.pubsub_to_gcs_bigquery import ParseJson, ValidateTransaction, TransformTransaction
from batch.gcs_transform_pipeline import ParseCSV, ParseJSON, CleanData, TransformTransactions


class TestParseJson(unittest.TestCase):
    """Test JSON parsing."""
    
    def setUp(self):
        self.parser = ParseJson()
    
    def test_valid_json(self):
        """Test parsing valid JSON."""
        message = b'{"transaction_id": "123", "customer_id": "456", "amount": 100.0}'
        result = list(self.parser.process(message))
        self.assertEqual(len(result), 1)
        self.assertIn('transaction_id', result[0])
        self.assertIn('processing_timestamp', result[0])
    
    def test_invalid_json(self):
        """Test parsing invalid JSON."""
        message = b'invalid json'
        result = list(self.parser.process(message))
        self.assertEqual(len(result), 1)
        self.assertIn('error', result[0])


class TestValidateTransaction(unittest.TestCase):
    """Test transaction validation."""
    
    def setUp(self):
        self.validator = ValidateTransaction()
    
    def test_valid_transaction(self):
        """Test valid transaction."""
        transaction = {
            'transaction_id': '123',
            'customer_id': '456',
            'product_id': '789',
            'amount': 100.0,
            'timestamp': '2024-01-01T00:00:00'
        }
        result = list(self.validator.process(transaction))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], transaction)
    
    def test_missing_fields(self):
        """Test transaction with missing fields."""
        transaction = {
            'transaction_id': '123',
            'amount': 100.0
        }
        result = list(self.validator.process(transaction))
        self.assertEqual(len(result), 0)
    
    def test_negative_amount(self):
        """Test transaction with negative amount."""
        transaction = {
            'transaction_id': '123',
            'customer_id': '456',
            'product_id': '789',
            'amount': -100.0,
            'timestamp': '2024-01-01T00:00:00'
        }
        result = list(self.validator.process(transaction))
        self.assertEqual(len(result), 0)


class TestTransformTransaction(unittest.TestCase):
    """Test transaction transformation."""
    
    def setUp(self):
        self.transformer = TransformTransaction()
    
    def test_transform(self):
        """Test transaction transformation."""
        transaction = {
            'transaction_id': '123',
            'customer_id': '456',
            'product_id': '789',
            'store_id': '101',
            'timestamp': '2024-01-01T00:00:00',
            'quantity': 2,
            'unit_price': 50.0,
            'amount': 100.0,
            'payment_method': 'CREDIT_CARD'
        }
        result = list(self.transformer.process(transaction))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['transaction_id'], '123')
        self.assertIn('load_timestamp', result[0])


class TestParseCSV(unittest.TestCase):
    """Test CSV parsing."""
    
    def setUp(self):
        self.parser = ParseCSV()
    
    def test_valid_csv(self):
        """Test parsing valid CSV."""
        csv_data = "id,name,value\n1,test,100\n2,test2,200"
        result = list(self.parser.process(csv_data))
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['id'], '1')
        self.assertEqual(result[0]['name'], 'test')


class TestParseJSON(unittest.TestCase):
    """Test JSON parsing for batch."""
    
    def setUp(self):
        self.parser = ParseJSON()
    
    def test_valid_json_object(self):
        """Test parsing JSON object."""
        json_data = '{"id": "1", "name": "test"}'
        result = list(self.parser.process(json_data))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], '1')
    
    def test_valid_json_array(self):
        """Test parsing JSON array."""
        json_data = '[{"id": "1"}, {"id": "2"}]'
        result = list(self.parser.process(json_data))
        self.assertEqual(len(result), 2)


class TestCleanData(unittest.TestCase):
    """Test data cleaning."""
    
    def setUp(self):
        self.cleaner = CleanData()
    
    def test_clean_data(self):
        """Test data cleaning."""
        data = {
            'Transaction ID': '123',
            'Customer ID': '456',
            'Amount': '100.0',
            'Description': '  test  '
        }
        result = list(self.cleaner.process(data))
        self.assertEqual(len(result), 1)
        self.assertIn('transaction_id', result[0])
        self.assertIn('load_timestamp', result[0])
        self.assertEqual(result[0]['description'], 'test')


class TestTransformTransactions(unittest.TestCase):
    """Test transaction transformation for batch."""
    
    def setUp(self):
        self.transformer = TransformTransactions()
    
    def test_transform(self):
        """Test transformation."""
        data = {
            'transaction_id': '123',
            'customer_id': '456',
            'product_id': '789',
            'timestamp': '2024-01-01 00:00:00',
            'amount': '100.0',
            'quantity': '2'
        }
        result = list(self.transformer.process(data))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['transaction_id'], '123')
        self.assertEqual(result[0]['quantity'], 2)
        self.assertEqual(result[0]['total_amount'], 100.0)


if __name__ == '__main__':
    unittest.main()


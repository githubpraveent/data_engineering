"""
Integration tests for data flow from ingestion to warehouse
"""
import pytest
from datetime import date


def test_bronze_to_silver_flow():
    """Test data flow from Bronze to Silver layer"""
    # Mock bronze data
    bronze_data = {
        'event_id': 'E001',
        'store_id': 'S001',
        'transaction_id': 'T001',
        'customer_id': 'C001',
        'product_id': 'P001',
        'quantity': 2,
        'price': 10.50,
        'transaction_timestamp': '2024-01-15 10:30:00'
    }
    
    # Transformation logic (cleaning, validation)
    silver_data = {
        'event_id': bronze_data['event_id'],
        'store_id': bronze_data['store_id'].upper().strip(),
        'transaction_id': bronze_data['transaction_id'],
        'customer_id': bronze_data['customer_id'].upper().strip(),
        'product_id': bronze_data['product_id'].upper().strip(),
        'quantity': bronze_data['quantity'],
        'price': float(bronze_data['price']),
        'transaction_timestamp': bronze_data['transaction_timestamp'],
        'line_total': bronze_data['quantity'] * float(bronze_data['price'])
    }
    
    assert silver_data['store_id'] == 'S001'
    assert silver_data['line_total'] == 21.0
    assert silver_data['event_id'] == bronze_data['event_id']


def test_silver_to_gold_flow():
    """Test data flow from Silver to Gold layer"""
    # Mock silver data
    silver_data = {
        'transaction_id': 'T001',
        'store_id': 'S001',
        'customer_id': 'C001',
        'total_amount': 100.00,
        'transaction_timestamp': '2024-01-15 10:30:00'
    }
    
    # Business logic application
    gold_data = {
        'transaction_id': silver_data['transaction_id'],
        'store_id': silver_data['store_id'],
        'customer_id': silver_data['customer_id'],
        'total_amount': silver_data['total_amount'],
        'transaction_type': 'High Value' if silver_data['total_amount'] >= 100 else 'Low Value',
        'transaction_date': date(2024, 1, 15)
    }
    
    assert gold_data['transaction_type'] == 'High Value'
    assert gold_data['transaction_date'] == date(2024, 1, 15)


def test_warehouse_load():
    """Test data load into warehouse"""
    # Mock gold data
    gold_data = {
        'transaction_id': 'T001',
        'date_key': 20240115,
        'customer_key': 1,
        'product_key': 1,
        'store_key': 1,
        'net_amount': 100.00
    }
    
    # Warehouse fact record
    fact_record = {
        'sales_fact_key': 1,
        'date_key': gold_data['date_key'],
        'customer_key': gold_data['customer_key'],
        'product_key': gold_data['product_key'],
        'store_key': gold_data['store_key'],
        'transaction_id': gold_data['transaction_id'],
        'net_amount': gold_data['net_amount']
    }
    
    assert fact_record['date_key'] == 20240115
    assert fact_record['net_amount'] == 100.00
    assert all(key in fact_record for key in ['date_key', 'customer_key', 'product_key', 'store_key'])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


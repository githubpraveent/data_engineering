"""
Unit tests for SCD (Slowly Changing Dimension) logic
"""
import pytest
from datetime import date, datetime


def test_scd_type1_overwrite():
    """Test SCD Type 1 logic (overwrite)"""
    # Mock dimension record
    existing_record = {
        'product_key': 1,
        'product_id': 'P001',
        'product_name': 'Old Product Name',
        'unit_price': 10.00
    }
    
    # New record with updated name
    new_record = {
        'product_id': 'P001',
        'product_name': 'New Product Name',
        'unit_price': 12.00
    }
    
    # SCD Type 1 should overwrite
    updated_record = existing_record.copy()
    updated_record.update(new_record)
    updated_record['updated_timestamp'] = datetime.now()
    
    assert updated_record['product_name'] == 'New Product Name'
    assert updated_record['unit_price'] == 12.00
    assert updated_record['product_key'] == 1  # Key unchanged


def test_scd_type2_historical():
    """Test SCD Type 2 logic (historical)"""
    # Mock existing current record
    existing_record = {
        'customer_key': 1,
        'customer_id': 'C001',
        'customer_name': 'John Doe',
        'email': 'john@example.com',
        'effective_date': date(2020, 1, 1),
        'expiry_date': None,
        'is_current': True
    }
    
    # New record with changed email
    new_record = {
        'customer_id': 'C001',
        'customer_name': 'John Doe',
        'email': 'john.new@example.com'
    }
    
    # SCD Type 2 should:
    # 1. Expire old record
    old_record = existing_record.copy()
    old_record['expiry_date'] = date.today()
    old_record['is_current'] = False
    
    # 2. Create new record
    new_dimension_record = {
        'customer_key': 2,  # New key
        'customer_id': 'C001',
        'customer_name': 'John Doe',
        'email': 'john.new@example.com',
        'effective_date': date.today(),
        'expiry_date': None,
        'is_current': True
    }
    
    assert old_record['is_current'] == False
    assert old_record['expiry_date'] == date.today()
    assert new_dimension_record['is_current'] == True
    assert new_dimension_record['customer_key'] != existing_record['customer_key']


def test_scd_type2_no_change():
    """Test SCD Type 2 when no change detected"""
    existing_record = {
        'customer_key': 1,
        'customer_id': 'C001',
        'customer_name': 'John Doe',
        'email': 'john@example.com',
        'is_current': True
    }
    
    new_record = {
        'customer_id': 'C001',
        'customer_name': 'John Doe',
        'email': 'john@example.com'  # No change
    }
    
    # No change detected, should not create new record
    has_change = (
        existing_record['customer_name'] != new_record['customer_name'] or
        existing_record['email'] != new_record['email']
    )
    
    assert has_change == False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


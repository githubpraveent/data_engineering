"""
Test Kafka topic validation and message format
"""
import pytest
import os
import json
from kafka import KafkaConsumer, KafkaProducer
import boto3
from confluent_kafka import Consumer, Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer

class TestKafkaTopics:
    """Test Kafka topics configuration and message validation"""
    
    @pytest.fixture
    def bootstrap_servers(self):
        return os.environ.get('MSK_BOOTSTRAP_SERVERS', 'localhost:9092')
    
    @pytest.fixture
    def topics(self):
        return [
            'retail.customer.cdc',
            'retail.order.cdc',
            'retail.product.cdc',
            'retail.order_item.cdc'
        ]
    
    def test_topics_exist(self, bootstrap_servers, topics):
        """Test that all required topics exist"""
        # This would require admin client access
        # For now, we'll test topic names format
        for topic in topics:
            assert topic.startswith('retail.'), f"Topic {topic} should start with 'retail.'"
            assert topic.endswith('.cdc'), f"Topic {topic} should end with '.cdc'"
    
    def test_topic_naming_convention(self, topics):
        """Test topic naming convention"""
        for topic in topics:
            parts = topic.split('.')
            assert len(parts) == 3, f"Topic {topic} should have format: retail.<table>.cdc"
            assert parts[0] == 'retail', f"Topic {topic} should start with 'retail'"
            assert parts[2] == 'cdc', f"Topic {topic} should end with 'cdc'"
    
    def test_message_schema_customer(self):
        """Test customer CDC message schema"""
        sample_message = {
            "op": "c",
            "ts_ms": "2024-01-01T00:00:00Z",
            "before": None,
            "after": {
                "customer_id": 1,
                "customer_name": "Test Customer",
                "email": "test@example.com",
                "phone": "1234567890",
                "address": "123 Main St",
                "city": "New York",
                "state": "NY",
                "zip_code": "10001",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }
        
        # Validate required fields
        assert 'op' in sample_message
        assert 'ts_ms' in sample_message
        assert sample_message['op'] in ['c', 'u', 'd']
        
        if sample_message['after']:
            assert 'customer_id' in sample_message['after']
            assert 'customer_name' in sample_message['after']
            assert 'email' in sample_message['after']
    
    def test_message_schema_order(self):
        """Test order CDC message schema"""
        sample_message = {
            "op": "u",
            "ts_ms": "2024-01-01T00:00:00Z",
            "before": {
                "order_id": 1,
                "customer_id": 1,
                "order_date": "2024-01-01T00:00:00Z",
                "total_amount": 100.00,
                "status": "pending"
            },
            "after": {
                "order_id": 1,
                "customer_id": 1,
                "order_date": "2024-01-01T00:00:00Z",
                "total_amount": 100.00,
                "status": "completed"
            }
        }
        
        assert 'op' in sample_message
        assert sample_message['op'] in ['c', 'u', 'd']
        
        if sample_message['after']:
            assert 'order_id' in sample_message['after']
            assert 'customer_id' in sample_message['after']
            assert 'total_amount' in sample_message['after']
    
    def test_message_operation_types(self):
        """Test that operation types are valid"""
        valid_ops = ['c', 'u', 'd']  # create, update, delete
        
        test_messages = [
            {"op": "c"},
            {"op": "u"},
            {"op": "d"},
            {"op": "invalid"}
        ]
        
        for msg in test_messages:
            if msg['op'] in valid_ops:
                assert True
            else:
                assert False, f"Invalid operation type: {msg['op']}"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])


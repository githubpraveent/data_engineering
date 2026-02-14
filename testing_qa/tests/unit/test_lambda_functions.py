"""
Unit tests for Lambda function business logic
"""
import pytest
from unittest.mock import Mock, patch
from framework.lambda.tester import LambdaTester
from framework.config import get_config


@pytest.mark.unit
class TestLambdaFunctions:
    """Test Lambda functions in isolation"""
    
    def test_process_order_lambda(self, lambda_invoker, test_data):
        """Test processOrder Lambda function"""
        # Load test data
        payload = test_data.get_template("order_payload", order_id="test-123")
        
        # Get function name from config
        config = get_config()
        function_name = config.lambda_config["functions"]["processOrder"]
        
        # Invoke Lambda
        response = lambda_invoker.invoke_sync(function_name, payload)
        
        # Assertions
        assert response["StatusCode"] == 200
        assert "FunctionError" not in response
        assert "Payload" in response
        
        payload_data = response["Payload"]
        assert payload_data.get("status") == "processed"
    
    def test_send_notification_lambda(self, lambda_invoker, test_data):
        """Test sendNotification Lambda function"""
        payload = test_data.get_template("notification_payload", message="Test notification")
        
        config = get_config()
        function_name = config.lambda_config["functions"]["sendNotification"]
        
        response = lambda_invoker.invoke_sync(function_name, payload)
        
        assert response["StatusCode"] == 200
        assert "FunctionError" not in response


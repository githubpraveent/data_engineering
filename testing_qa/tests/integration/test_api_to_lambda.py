"""
Integration tests: API Gateway -> Lambda
"""
import pytest
import time
from framework.api.client import APIClient
from framework.api.validator import ResponseValidator
from framework.async.polling import PollingVerifier
from framework.async.state_checker import StateChecker
from framework.config import get_config


@pytest.mark.integration
class TestAPIToLambda:
    """Test API Gateway to Lambda integration"""
    
    def test_create_order_sync(self, api_client, test_data):
        """Test synchronous order creation via API"""
        # Prepare request
        order_data = test_data.get_template("order_payload", order_id=f"test-{int(time.time())}")
        
        # Make API call
        response = api_client.post("/orders", json=order_data)
        
        # Validate immediate response
        validator = ResponseValidator()
        assert validator.validate_status_code(response, 201)
        assert validator.validate_json_path(response, "orderId")
        assert validator.validate_json_path(response, "status", "pending")
        
        response_data = response.json()
        order_id = response_data["orderId"]
        
        # Verify order was created (check downstream state)
        state_checker = StateChecker()
        # This would check DynamoDB or other storage
        # assert state_checker.check_dynamodb_item("orders", {"orderId": order_id})
    
    @pytest.mark.async
    def test_create_order_async(self, api_client, test_data):
        """Test asynchronous order processing via API"""
        # Create order
        order_data = test_data.get_template("order_payload", order_id=f"test-async-{int(time.time())}")
        response = api_client.post("/orders", json=order_data)
        
        assert response.status_code == 202  # Accepted
        response_data = response.json()
        order_id = response_data["orderId"]
        
        # Wait for async processing
        poller = PollingVerifier(
            poll_interval=2,
            max_wait_time=60
        )
        
        def check_order_processed():
            # Check order status via API
            status_response = api_client.get(f"/orders/{order_id}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                return status_data.get("status") == "processed"
            return False
        
        # Poll until order is processed
        assert poller.poll_until(
            check_order_processed,
            f"Order {order_id} processed",
            f"Order {order_id} not processed within timeout"
        )
    
    @pytest.mark.async
    def test_order_with_queue_verification(self, api_client, test_data):
        """Test order creation and verify message in queue"""
        order_data = test_data.get_template("order_payload", order_id=f"test-queue-{int(time.time())}")
        response = api_client.post("/orders", json=order_data)
        
        assert response.status_code == 202
        order_id = response.json()["orderId"]
        
        # Verify message in queue
        config = get_config()
        queue_url = config.queues.get("orderQueue")
        
        if queue_url:
            state_checker = StateChecker()
            poller = PollingVerifier()
            
            def check_queue_message():
                message = state_checker.check_queue_message(
                    queue_url,
                    lambda msg: msg.get("orderId") == order_id
                )
                return message is not None
            
            assert poller.poll_until(
                check_queue_message,
                f"Message found in queue for order {order_id}",
                f"Message not found in queue for order {order_id}"
            )


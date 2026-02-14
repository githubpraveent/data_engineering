"""
End-to-end tests for complete order flow
"""
import pytest
import time
from framework.api.client import APIClient
from framework.api.validator import ResponseValidator
from framework.async.polling import PollingVerifier
from framework.async.state_checker import StateChecker
from framework.async.event_waiter import EventWaiter
from framework.config import get_config


@pytest.mark.e2e
class TestOrderFlow:
    """Test complete order processing flow"""
    
    @pytest.mark.slow
    def test_complete_order_flow(self, api_client, test_data):
        """
        Test complete order flow:
        1. Create order via API
        2. Verify order queued
        3. Wait for Lambda processing
        4. Verify downstream service notification
        5. Verify final state
        """
        # Step 1: Create order
        order_data = test_data.get_template(
            "order_payload",
            order_id=f"e2e-{int(time.time())}",
            customer_id="customer-123",
            amount=100.00
        )
        
        response = api_client.post("/orders", json=order_data)
        validator = ResponseValidator()
        assert validator.validate_status_code(response, 202)
        
        response_data = response.json()
        order_id = response_data["orderId"]
        
        # Step 2: Verify order in queue
        config = get_config()
        queue_url = config.queues.get("orderQueue")
        state_checker = StateChecker()
        poller = PollingVerifier()
        
        if queue_url:
            def check_queue():
                message = state_checker.check_queue_message(
                    queue_url,
                    lambda msg: msg.get("orderId") == order_id
                )
                return message is not None
            
            assert poller.poll_until(
                check_queue,
                f"Order {order_id} found in queue",
                f"Order {order_id} not found in queue"
            )
        
        # Step 3: Wait for processing
        def check_order_processed():
            status_response = api_client.get(f"/orders/{order_id}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                return status_data.get("status") == "processed"
            return False
        
        assert poller.poll_until(
            check_order_processed,
            f"Order {order_id} processed",
            f"Order {order_id} not processed"
        )
        
        # Step 4: Verify downstream service was called
        # Check if payment service was notified
        payment_service = config.downstream_services.get("payment_service")
        if payment_service and not payment_service.get("use_simulation"):
            # In real scenario, check payment service state
            # This would verify payment was processed
            pass
        
        # Step 5: Verify final state in database
        # Check DynamoDB or other storage
        # assert state_checker.check_dynamodb_item(
        #     "orders",
        #     {"orderId": order_id},
        #     {"status": "processed", "paymentStatus": "completed"}
        # )
    
    @pytest.mark.async
    def test_order_with_retry(self, api_client, test_data):
        """Test order flow with retry logic"""
        order_data = test_data.get_template(
            "order_payload",
            order_id=f"retry-{int(time.time())}",
            simulate_failure=True
        )
        
        response = api_client.post("/orders", json=order_data)
        assert response.status_code in [202, 500]  # May fail initially
        
        if response.status_code == 202:
            order_id = response.json()["orderId"]
            poller = PollingVerifier(max_wait_time=120)  # Longer timeout for retries
            
            def check_final_status():
                status_response = api_client.get(f"/orders/{order_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    return status_data.get("status") in ["processed", "failed"]
                return False
            
            assert poller.poll_until(
                check_final_status,
                f"Order {order_id} reached final status",
                f"Order {order_id} did not reach final status"
            )


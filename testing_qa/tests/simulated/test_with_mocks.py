"""
Tests using API simulation for downstream services
"""
import pytest
import time
from framework.api.client import APIClient
from framework.simulation.mock_server import MockServer
from framework.config import get_config


@pytest.mark.simulated
class TestWithMocks:
    """Test with mocked downstream services"""
    
    def test_order_with_mocked_payment_service(self, api_client, mock_server, test_data):
        """Test order flow with mocked payment service"""
        config = get_config()
        payment_service = config.downstream_services.get("payment_service")
        
        if not payment_service or not payment_service.get("use_simulation"):
            pytest.skip("Payment service simulation not configured")
        
        # Start payment service simulation
        simulator = mock_server.start_service_simulation("payment_service")
        
        # Register mock endpoint
        simulator.register_endpoint(
            "/payment/process",
            method="POST",
            response={"status": "success", "transactionId": "txn-123"},
            status_code=200
        )
        
        # Create order
        order_data = test_data.get_template("order_payload", order_id=f"mock-{int(time.time())}")
        response = api_client.post("/orders", json=order_data)
        
        assert response.status_code == 202
        
        # Wait a bit for async processing
        time.sleep(5)
        
        # Verify payment service was called
        payment_requests = simulator.get_request_history(path="/payment/process", method="POST")
        assert len(payment_requests) > 0
        
        # Verify request payload
        payment_request = payment_requests[0]
        assert payment_request["json"]["orderId"] == order_data["orderId"]
    
    def test_order_with_delayed_response(self, api_client, mock_server, test_data):
        """Test handling of delayed downstream service responses"""
        simulator = mock_server.start_service_simulation("payment_service")
        
        # Register endpoint with delay
        simulator.register_endpoint(
            "/payment/process",
            method="POST",
            response={"status": "success"},
            status_code=200,
            delay=3.0  # 3 second delay
        )
        
        order_data = test_data.get_template("order_payload", order_id=f"delay-{int(time.time())}")
        response = api_client.post("/orders", json=order_data)
        
        assert response.status_code == 202
        
        # Wait for delayed processing
        time.sleep(10)
        
        # Verify service was called
        requests = simulator.get_request_history(path="/payment/process")
        assert len(requests) > 0


"""
Event waiting utilities for async operations
"""
import time
import logging
from typing import Dict, Any, Callable, Optional
import boto3
from framework.config import get_config
from framework.async.polling import PollingVerifier

logger = logging.getLogger(__name__)


class EventWaiter:
    """Waits for events in async/event-driven systems"""
    
    def __init__(self, poll_interval: float = 2, max_wait_time: float = 60):
        self.config = get_config()
        self.poll_verifier = PollingVerifier(poll_interval, max_wait_time)
        self.aws_region = self.config.aws_config.get("region", "us-east-1")
        self._eventbridge_client = None
    
    @property
    def eventbridge_client(self):
        """Get EventBridge client"""
        if self._eventbridge_client is None:
            self._eventbridge_client = boto3.client('events', region_name=self.aws_region)
        return self._eventbridge_client
    
    def wait_for_event(
        self,
        event_bus_name: str,
        event_pattern: Dict[str, Any],
        event_validator: Callable[[Dict[str, Any]], bool] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Wait for event matching pattern on EventBridge
        
        Note: This is a simplified implementation. In practice, you might need
        to use EventBridge rules, CloudWatch Logs, or a custom event listener.
        """
        logger.info(f"Waiting for event on bus {event_bus_name} with pattern {event_pattern}")
        
        # This is a placeholder - actual implementation would depend on
        # how events are captured (CloudWatch Logs, SQS, custom listener, etc.)
        def check_event():
            # In real implementation, this would query EventBridge or
            # check a captured event store
            return None
        
        return self.poll_verifier.poll_until_not_none(
            check_event,
            f"Event received on {event_bus_name}",
            f"Event not received on {event_bus_name} within timeout"
        )
    
    def wait_for_lambda_completion(
        self,
        function_name: str,
        invocation_id: str,
        completion_checker: Callable[[str, str], bool]
    ) -> bool:
        """Wait for Lambda function to complete"""
        logger.info(f"Waiting for Lambda {function_name} invocation {invocation_id} to complete")
        
        def check_completion():
            return completion_checker(function_name, invocation_id)
        
        return self.poll_verifier.poll_until(
            check_completion,
            f"Lambda {function_name} completed",
            f"Lambda {function_name} did not complete within timeout"
        )
    
    def wait_for_downstream_service(
        self,
        service_name: str,
        check_func: Callable[[], bool],
        context: Dict[str, Any] = None
    ) -> bool:
        """Wait for downstream service to be ready/updated"""
        logger.info(f"Waiting for downstream service {service_name}")
        
        return self.poll_verifier.poll_until(
            check_func,
            f"Downstream service {service_name} ready",
            f"Downstream service {service_name} not ready within timeout",
            context
        )


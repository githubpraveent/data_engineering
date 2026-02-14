"""
Polling utilities for async/event-driven testing
"""
import time
import logging
from typing import Callable, Optional, Any, Dict
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_result

logger = logging.getLogger(__name__)


class PollingVerifier:
    """Verifies async operations by polling"""
    
    def __init__(self, poll_interval: float = 2, max_wait_time: float = 60):
        self.poll_interval = poll_interval
        self.max_wait_time = max_wait_time
        self.max_attempts = int(max_wait_time / poll_interval)
    
    def poll_until(
        self,
        condition: Callable[[], bool],
        success_message: str = "Condition met",
        failure_message: str = "Condition not met within timeout",
        context: Dict[str, Any] = None
    ) -> bool:
        """
        Poll until condition is met or timeout
        
        Args:
            condition: Function that returns True when condition is met
            success_message: Message to log on success
            failure_message: Message to log on failure
            context: Additional context for logging
        
        Returns:
            True if condition met, False if timeout
        """
        start_time = time.time()
        attempt = 0
        
        while time.time() - start_time < self.max_wait_time:
            attempt += 1
            try:
                if condition():
                    elapsed = time.time() - start_time
                    logger.info(f"{success_message} (attempt {attempt}, {elapsed:.2f}s)")
                    if context:
                        logger.debug(f"Context: {context}")
                    return True
            except Exception as e:
                logger.warning(f"Error checking condition (attempt {attempt}): {e}")
            
            if attempt < self.max_attempts:
                time.sleep(self.poll_interval)
        
        elapsed = time.time() - start_time
        logger.error(f"{failure_message} (attempted {attempt} times, {elapsed:.2f}s)")
        return False
    
    def poll_until_value(
        self,
        get_value: Callable[[], Any],
        expected_value: Any,
        success_message: str = None,
        failure_message: str = None
    ) -> bool:
        """Poll until value matches expected"""
        success_msg = success_message or f"Value matches expected: {expected_value}"
        failure_msg = failure_message or f"Value did not match {expected_value} within timeout"
        
        def condition():
            value = get_value()
            logger.debug(f"Polled value: {value}, expected: {expected_value}")
            return value == expected_value
        
        return self.poll_until(condition, success_msg, failure_msg)
    
    def poll_until_not_none(
        self,
        get_value: Callable[[], Any],
        success_message: str = None,
        failure_message: str = None
    ) -> Any:
        """Poll until value is not None, return the value"""
        success_msg = success_message or "Value is not None"
        failure_msg = failure_message or "Value is None within timeout"
        
        value = None
        
        def condition():
            nonlocal value
            value = get_value()
            return value is not None
        
        if self.poll_until(condition, success_msg, failure_msg):
            return value
        return None
    
    def poll_with_retry(
        self,
        operation: Callable[[], Any],
        validator: Callable[[Any], bool],
        max_retries: int = 3
    ) -> Optional[Any]:
        """Poll with retry logic for operations that may fail"""
        for retry_count in range(max_retries):
            try:
                result = operation()
                if validator(result):
                    return result
                logger.debug(f"Validation failed, retrying ({retry_count + 1}/{max_retries})")
            except Exception as e:
                logger.warning(f"Operation failed, retrying ({retry_count + 1}/{max_retries}): {e}")
            
            if retry_count < max_retries - 1:
                time.sleep(self.poll_interval)
        
        return None


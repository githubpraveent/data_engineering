"""
Retry Handler Utility
Provides retry logic with exponential backoff for Bigtable operations
"""

import time
import logging
from typing import Callable, Any, Optional, TypeVar
from functools import wraps
from retrying import retry
from google.api_core import exceptions as gcp_exceptions

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_on_transient_errors(
    stop_max_attempt_number: int = 5,
    wait_exponential_multiplier: int = 1000,
    wait_exponential_max: int = 10000,
):
    """
    Decorator for retrying functions on transient GCP errors

    Args:
        stop_max_attempt_number: Maximum number of retry attempts
        wait_exponential_multiplier: Base wait time in milliseconds
        wait_exponential_max: Maximum wait time in milliseconds
    """

    def retry_if_gcp_error(exception: Exception) -> bool:
        """Check if exception is a retryable GCP error"""
        retryable_exceptions = (
            gcp_exceptions.ServiceUnavailable,
            gcp_exceptions.InternalServerError,
            gcp_exceptions.DeadlineExceeded,
            gcp_exceptions.TooManyRequests,
            ConnectionError,
            TimeoutError,
        )
        return isinstance(exception, retryable_exceptions)

    def wrapper(func: Callable[..., T]) -> Callable[..., T]:
        @retry(
            stop_max_attempt_number=stop_max_attempt_number,
            wait_exponential_multiplier=wait_exponential_multiplier,
            wait_exponential_max=wait_exponential_max,
            retry_on_exception=retry_if_gcp_error,
        )
        @wraps(func)
        def wrapped(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(
                    f"Retrying {func.__name__} due to error: {str(e)}",
                    exc_info=True,
                )
                raise

        return wrapped

    return wrapper


class RetryHandler:
    """
    Retry handler class for Bigtable operations
    """

    def __init__(
        self,
        max_retries: int = 5,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
    ):
        """
        Initialize retry handler

        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base

    def _is_retryable_error(self, error: Exception) -> bool:
        """Check if error is retryable"""
        retryable_exceptions = (
            gcp_exceptions.ServiceUnavailable,
            gcp_exceptions.InternalServerError,
            gcp_exceptions.DeadlineExceeded,
            gcp_exceptions.TooManyRequests,
            ConnectionError,
            TimeoutError,
            OSError,  # Network errors
        )
        return isinstance(error, retryable_exceptions)

    def execute_with_retry(
        self, func: Callable[..., T], *args: Any, **kwargs: Any
    ) -> T:
        """
        Execute a function with retry logic

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function return value

        Raises:
            Last exception if all retries fail
        """
        last_exception = None
        delay = self.initial_delay

        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e

                if not self._is_retryable_error(e):
                    # Non-retryable error, raise immediately
                    logger.error(f"Non-retryable error in {func.__name__}: {str(e)}")
                    raise

                if attempt < self.max_retries - 1:
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries} failed for {func.__name__}: {str(e)}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    time.sleep(delay)
                    delay = min(delay * self.exponential_base, self.max_delay)
                else:
                    logger.error(
                        f"All {self.max_retries} attempts failed for {func.__name__}"
                    )

        # All retries exhausted
        if last_exception:
            logger.error(
                f"Exhausted all retries for {func.__name__}. Raising last exception."
            )
            raise last_exception

        raise RuntimeError("Unexpected error in retry handler")

"""
API Client for testing API Gateway endpoints
"""
import time
import logging
from typing import Dict, Any, Optional, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from framework.config import get_config

logger = logging.getLogger(__name__)


class APIClient:
    """Client for making API requests to API Gateway"""
    
    def __init__(self, base_url: str = None, api_key: str = None, timeout: int = None):
        self.config = get_config()
        self.base_url = base_url or self.config.api_gateway.get("base_url")
        self.api_key = api_key or self.config.api_gateway.get("api_key")
        self.timeout = timeout or self.config.api_gateway.get("timeout", 30)
        self.retry_attempts = self.config.api_gateway.get("retry_attempts", 3)
        
        # Setup session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=self.retry_attempts,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        if self.api_key:
            self.session.headers.update({
                "x-api-key": self.api_key,
                "Content-Type": "application/json"
            })
    
    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint"""
        endpoint = endpoint.lstrip("/")
        return f"{self.base_url.rstrip('/')}/{endpoint}"
    
    def get(self, endpoint: str, params: Dict = None, headers: Dict = None, **kwargs) -> requests.Response:
        """Make GET request"""
        url = self._build_url(endpoint)
        merged_headers = {**self.session.headers, **(headers or {})}
        logger.info(f"GET {url}")
        return self.session.get(url, params=params, headers=merged_headers, timeout=self.timeout, **kwargs)
    
    def post(self, endpoint: str, data: Any = None, json: Dict = None, headers: Dict = None, **kwargs) -> requests.Response:
        """Make POST request"""
        url = self._build_url(endpoint)
        merged_headers = {**self.session.headers, **(headers or {})}
        logger.info(f"POST {url}")
        if json:
            logger.debug(f"Request body: {json}")
        return self.session.post(url, data=data, json=json, headers=merged_headers, timeout=self.timeout, **kwargs)
    
    def put(self, endpoint: str, data: Any = None, json: Dict = None, headers: Dict = None, **kwargs) -> requests.Response:
        """Make PUT request"""
        url = self._build_url(endpoint)
        merged_headers = {**self.session.headers, **(headers or {})}
        logger.info(f"PUT {url}")
        return self.session.put(url, data=data, json=json, headers=merged_headers, timeout=self.timeout, **kwargs)
    
    def delete(self, endpoint: str, headers: Dict = None, **kwargs) -> requests.Response:
        """Make DELETE request"""
        url = self._build_url(endpoint)
        merged_headers = {**self.session.headers, **(headers or {})}
        logger.info(f"DELETE {url}")
        return self.session.delete(url, headers=merged_headers, timeout=self.timeout, **kwargs)
    
    def patch(self, endpoint: str, data: Any = None, json: Dict = None, headers: Dict = None, **kwargs) -> requests.Response:
        """Make PATCH request"""
        url = self._build_url(endpoint)
        merged_headers = {**self.session.headers, **(headers or {})}
        logger.info(f"PATCH {url}")
        return self.session.patch(url, data=data, json=json, headers=merged_headers, timeout=self.timeout, **kwargs)
    
    def request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make custom request"""
        url = self._build_url(endpoint)
        logger.info(f"{method} {url}")
        return self.session.request(method, url, timeout=self.timeout, **kwargs)


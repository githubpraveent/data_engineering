"""
Request builder for constructing API requests
"""
from typing import Dict, Any, Optional
from framework.api.client import APIClient


class RequestBuilder:
    """Builder pattern for constructing API requests"""
    
    def __init__(self, client: APIClient = None):
        self.client = client or APIClient()
        self._endpoint: Optional[str] = None
        self._method: str = "GET"
        self._headers: Dict[str, str] = {}
        self._params: Dict[str, Any] = {}
        self._json: Optional[Dict[str, Any]] = {}
        self._data: Optional[Any] = None
    
    def endpoint(self, endpoint: str) -> 'RequestBuilder':
        """Set endpoint"""
        self._endpoint = endpoint
        return self
    
    def method(self, method: str) -> 'RequestBuilder':
        """Set HTTP method"""
        self._method = method.upper()
        return self
    
    def header(self, key: str, value: str) -> 'RequestBuilder':
        """Add header"""
        self._headers[key] = value
        return self
    
    def headers(self, headers: Dict[str, str]) -> 'RequestBuilder':
        """Set headers"""
        self._headers.update(headers)
        return self
    
    def param(self, key: str, value: Any) -> 'RequestBuilder':
        """Add query parameter"""
        self._params[key] = value
        return self
    
    def params(self, params: Dict[str, Any]) -> 'RequestBuilder':
        """Set query parameters"""
        self._params.update(params)
        return self
    
    def json_body(self, data: Dict[str, Any]) -> 'RequestBuilder':
        """Set JSON body"""
        self._json = data
        return self
    
    def body(self, data: Any) -> 'RequestBuilder':
        """Set raw body"""
        self._data = data
        return self
    
    def build(self):
        """Build and execute request"""
        if not self._endpoint:
            raise ValueError("Endpoint is required")
        
        kwargs = {
            "headers": self._headers if self._headers else None,
            **({"params": self._params} if self._params else {}),
            **({"json": self._json} if self._json else {}),
            **({"data": self._data} if self._data else {})
        }
        
        return self.client.request(self._method, self._endpoint, **kwargs)


"""
Response validation utilities
"""
import json
import logging
from typing import Dict, Any, Optional, List, Callable
import requests
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)


class ResponseValidator:
    """Validates API responses"""
    
    @staticmethod
    def validate_status_code(response: requests.Response, expected_code: int = 200) -> bool:
        """Validate HTTP status code"""
        if response.status_code != expected_code:
            logger.error(f"Expected status {expected_code}, got {response.status_code}")
            return False
        return True
    
    @staticmethod
    def validate_json_schema(response: requests.Response, schema: Dict[str, Any]) -> bool:
        """Validate response JSON against schema"""
        try:
            data = response.json()
            validate(instance=data, schema=schema)
            return True
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {e}")
            return False
        except ValidationError as e:
            logger.error(f"Schema validation failed: {e.message}")
            return False
    
    @staticmethod
    def validate_response_time(response: requests.Response, max_time_ms: int) -> bool:
        """Validate response time"""
        elapsed_ms = response.elapsed.total_seconds() * 1000
        if elapsed_ms > max_time_ms:
            logger.error(f"Response time {elapsed_ms}ms exceeds max {max_time_ms}ms")
            return False
        return True
    
    @staticmethod
    def validate_headers(response: requests.Response, expected_headers: Dict[str, str]) -> bool:
        """Validate response headers"""
        for header, expected_value in expected_headers.items():
            actual_value = response.headers.get(header)
            if actual_value != expected_value:
                logger.error(f"Header {header}: expected {expected_value}, got {actual_value}")
                return False
        return True
    
    @staticmethod
    def validate_json_path(response: requests.Response, json_path: str, expected_value: Any = None, 
                          validator: Callable = None) -> bool:
        """Validate value at JSON path"""
        try:
            data = response.json()
            keys = json_path.split('.')
            value = data
            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key)
                elif isinstance(value, list) and key.isdigit():
                    value = value[int(key)]
                else:
                    logger.error(f"Path {json_path} not found in response")
                    return False
            
            if validator:
                return validator(value)
            elif expected_value is not None:
                if value != expected_value:
                    logger.error(f"Path {json_path}: expected {expected_value}, got {value}")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error validating JSON path {json_path}: {e}")
            return False
    
    @staticmethod
    def validate_custom(response: requests.Response, validator_func: Callable[[requests.Response], bool]) -> bool:
        """Validate using custom validator function"""
        try:
            return validator_func(response)
        except Exception as e:
            logger.error(f"Custom validation failed: {e}")
            return False
    
    @classmethod
    def validate_all(cls, response: requests.Response, validations: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Run multiple validations and return results"""
        results = {}
        for validation in validations:
            validation_type = validation.get("type")
            validation_name = validation.get("name", validation_type)
            
            if validation_type == "status_code":
                results[validation_name] = cls.validate_status_code(
                    response, validation.get("expected", 200)
                )
            elif validation_type == "json_schema":
                results[validation_name] = cls.validate_json_schema(
                    response, validation.get("schema", {})
                )
            elif validation_type == "response_time":
                results[validation_name] = cls.validate_response_time(
                    response, validation.get("max_time_ms", 1000)
                )
            elif validation_type == "headers":
                results[validation_name] = cls.validate_headers(
                    response, validation.get("expected_headers", {})
                )
            elif validation_type == "json_path":
                results[validation_name] = cls.validate_json_path(
                    response,
                    validation.get("json_path"),
                    validation.get("expected_value"),
                    validation.get("validator")
                )
            elif validation_type == "custom":
                results[validation_name] = cls.validate_custom(
                    response, validation.get("validator_func")
                )
        
        return results


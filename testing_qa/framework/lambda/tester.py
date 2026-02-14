"""
Lambda testing utilities
"""
import logging
from typing import Dict, Any, Callable, Optional
from framework.lambda.invoker import LambdaInvoker
from framework.api.validator import ResponseValidator

logger = logging.getLogger(__name__)


class LambdaTester:
    """Test Lambda functions"""
    
    def __init__(self):
        self.invoker = LambdaInvoker()
        self.validator = ResponseValidator()
    
    def test_lambda(
        self,
        function_name: str,
        payload: Dict[str, Any],
        validators: list = None,
        expected_status: int = 200
    ) -> Dict[str, Any]:
        """
        Test Lambda function with validators
        
        Args:
            function_name: Name or ARN of Lambda function
            payload: Event payload
            validators: List of validator functions
            expected_status: Expected status code
        
        Returns:
            Test results
        """
        logger.info(f"Testing Lambda: {function_name}")
        
        # Invoke Lambda
        response = self.invoker.invoke_sync(function_name, payload)
        
        # Check status code
        status_code = response.get("StatusCode", 0)
        if status_code != expected_status:
            logger.error(f"Expected status {expected_status}, got {status_code}")
            return {
                "success": False,
                "status_code": status_code,
                "error": f"Status code mismatch: {status_code} != {expected_status}"
            }
        
        # Check for function errors
        if "FunctionError" in response:
            logger.error(f"Lambda function error: {response['FunctionError']}")
            return {
                "success": False,
                "function_error": response["FunctionError"],
                "payload": response.get("Payload")
            }
        
        # Run validators
        validation_results = {}
        if validators:
            payload_data = response.get("Payload", {})
            for validator in validators:
                if isinstance(validator, dict):
                    validator_type = validator.get("type")
                    validator_name = validator.get("name", validator_type)
                    
                    if validator_type == "custom":
                        validator_func = validator.get("validator_func")
                        if validator_func:
                            validation_results[validator_name] = validator_func(payload_data)
                    elif validator_type == "json_path":
                        # Custom JSON path validation for Lambda response
                        json_path = validator.get("json_path")
                        expected_value = validator.get("expected_value")
                        # Simple path traversal
                        value = payload_data
                        for key in json_path.split('.'):
                            if isinstance(value, dict):
                                value = value.get(key)
                            else:
                                value = None
                                break
                        validation_results[validator_name] = value == expected_value
                elif callable(validator):
                    validation_results[str(validator)] = validator(payload_data)
        
        success = all(validation_results.values()) if validation_results else True
        
        return {
            "success": success,
            "status_code": status_code,
            "payload": response.get("Payload"),
            "validation_results": validation_results
        }


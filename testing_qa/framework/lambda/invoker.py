"""
Lambda function invocation utilities
"""
import json
import logging
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError
from framework.config import get_config

logger = logging.getLogger(__name__)


class LambdaInvoker:
    """Invokes Lambda functions for testing"""
    
    def __init__(self, region: str = None):
        self.config = get_config()
        self.region = region or self.config.aws_config.get("region", "us-east-1")
        self._lambda_client = None
    
    @property
    def lambda_client(self):
        """Get Lambda client"""
        if self._lambda_client is None:
            self._lambda_client = boto3.client('lambda', region_name=self.region)
        return self._lambda_client
    
    def invoke(
        self,
        function_name: str,
        payload: Dict[str, Any] = None,
        invocation_type: str = "RequestResponse",
        qualifier: str = None
    ) -> Dict[str, Any]:
        """
        Invoke Lambda function
        
        Args:
            function_name: Name or ARN of Lambda function
            payload: Event payload
            invocation_type: RequestResponse or Event
            qualifier: Version or alias
        
        Returns:
            Response from Lambda
        """
        try:
            invoke_params = {
                "FunctionName": function_name,
                "InvocationType": invocation_type
            }
            
            if payload:
                invoke_params["Payload"] = json.dumps(payload)
            
            if qualifier:
                invoke_params["Qualifier"] = qualifier
            
            logger.info(f"Invoking Lambda: {function_name} (type: {invocation_type})")
            if payload:
                logger.debug(f"Payload: {payload}")
            
            response = self.lambda_client.invoke(**invoke_params)
            
            # Parse response
            result = {
                "StatusCode": response["StatusCode"],
                "ResponseMetadata": response.get("ResponseMetadata", {})
            }
            
            if "Payload" in response:
                payload_stream = response["Payload"]
                payload_data = payload_stream.read()
                if payload_data:
                    try:
                        result["Payload"] = json.loads(payload_data.decode('utf-8'))
                    except json.JSONDecodeError:
                        result["Payload"] = payload_data.decode('utf-8')
            
            if "FunctionError" in response:
                result["FunctionError"] = response["FunctionError"]
                logger.error(f"Lambda error: {result.get('FunctionError')}")
            
            if "ExecutedVersion" in response:
                result["ExecutedVersion"] = response["ExecutedVersion"]
            
            return result
            
        except ClientError as e:
            logger.error(f"Error invoking Lambda {function_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error invoking Lambda {function_name}: {e}")
            raise
    
    def invoke_sync(self, function_name: str, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        """Invoke Lambda synchronously"""
        return self.invoke(function_name, payload, invocation_type="RequestResponse")
    
    def invoke_async(self, function_name: str, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        """Invoke Lambda asynchronously"""
        return self.invoke(function_name, payload, invocation_type="Event")
    
    def get_function_config(self, function_name: str) -> Dict[str, Any]:
        """Get Lambda function configuration"""
        try:
            response = self.lambda_client.get_function_configuration(FunctionName=function_name)
            return response
        except ClientError as e:
            logger.error(f"Error getting Lambda config {function_name}: {e}")
            raise


"""
State verification utilities for async operations
"""
import logging
from typing import Dict, Any, Callable, Optional, List
import boto3
from framework.config import get_config

logger = logging.getLogger(__name__)


class StateChecker:
    """Checks final state after async operations"""
    
    def __init__(self):
        self.config = get_config()
        self.aws_region = self.config.aws_config.get("region", "us-east-1")
        self._sqs_client = None
        self._dynamodb_client = None
        self._s3_client = None
    
    @property
    def sqs_client(self):
        """Get SQS client"""
        if self._sqs_client is None:
            self._sqs_client = boto3.client('sqs', region_name=self.aws_region)
        return self._sqs_client
    
    @property
    def dynamodb_client(self):
        """Get DynamoDB client"""
        if self._dynamodb_client is None:
            self._dynamodb_client = boto3.client('dynamodb', region_name=self.aws_region)
        return self._dynamodb_client
    
    @property
    def s3_client(self):
        """Get S3 client"""
        if self._s3_client is None:
            self._s3_client = boto3.client('s3', region_name=self.aws_region)
        return self._s3_client
    
    def check_queue_message(
        self,
        queue_url: str,
        message_validator: Callable[[Dict[str, Any]], bool],
        max_messages: int = 10
    ) -> Optional[Dict[str, Any]]:
        """Check if message exists in queue matching validator"""
        try:
            response = self.sqs_client.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=max_messages,
                AttributeNames=['All'],
                MessageAttributeNames=['All']
            )
            
            messages = response.get('Messages', [])
            for message in messages:
                body = message.get('Body', '{}')
                if isinstance(body, str):
                    import json
                    body = json.loads(body)
                
                if message_validator(body):
                    logger.info(f"Found matching message in queue {queue_url}")
                    return message
            
            logger.debug(f"No matching message found in queue {queue_url}")
            return None
        except Exception as e:
            logger.error(f"Error checking queue {queue_url}: {e}")
            return None
    
    def check_dynamodb_item(
        self,
        table_name: str,
        key: Dict[str, Any],
        expected_attributes: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """Check if item exists in DynamoDB with expected attributes"""
        try:
            response = self.dynamodb_client.get_item(
                TableName=table_name,
                Key=key
            )
            
            item = response.get('Item')
            if item is None:
                logger.debug(f"Item not found in table {table_name} with key {key}")
                return None
            
            if expected_attributes:
                # Convert DynamoDB format to regular dict
                item_dict = self._dynamodb_to_dict(item)
                for attr, expected_value in expected_attributes.items():
                    if item_dict.get(attr) != expected_value:
                        logger.debug(
                            f"Attribute {attr} mismatch: expected {expected_value}, "
                            f"got {item_dict.get(attr)}"
                        )
                        return None
            
            logger.info(f"Item found in table {table_name} with matching attributes")
            return item
        except Exception as e:
            logger.error(f"Error checking DynamoDB table {table_name}: {e}")
            return None
    
    def check_s3_object(
        self,
        bucket: str,
        key: str,
        expected_metadata: Dict[str, str] = None
    ) -> bool:
        """Check if S3 object exists with expected metadata"""
        try:
            response = self.s3_client.head_object(Bucket=bucket, Key=key)
            
            if expected_metadata:
                metadata = response.get('Metadata', {})
                for meta_key, expected_value in expected_metadata.items():
                    if metadata.get(meta_key) != expected_value:
                        logger.debug(
                            f"Metadata {meta_key} mismatch: expected {expected_value}, "
                            f"got {metadata.get(meta_key)}"
                        )
                        return False
            
            logger.info(f"Object found in S3: s3://{bucket}/{key}")
            return True
        except self.s3_client.exceptions.NoSuchKey:
            logger.debug(f"Object not found in S3: s3://{bucket}/{key}")
            return False
        except Exception as e:
            logger.error(f"Error checking S3 object s3://{bucket}/{key}: {e}")
            return False
    
    def check_custom_state(
        self,
        checker_func: Callable[[], bool],
        context: Dict[str, Any] = None
    ) -> bool:
        """Check custom state using provided function"""
        try:
            result = checker_func()
            if result:
                logger.info("Custom state check passed")
                if context:
                    logger.debug(f"Context: {context}")
            else:
                logger.debug("Custom state check failed")
            return result
        except Exception as e:
            logger.error(f"Error in custom state check: {e}")
            return False
    
    def _dynamodb_to_dict(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Convert DynamoDB item format to regular dict"""
        result = {}
        for key, value in item.items():
            if 'S' in value:
                result[key] = value['S']
            elif 'N' in value:
                result[key] = int(value['N']) if value['N'].isdigit() else float(value['N'])
            elif 'BOOL' in value:
                result[key] = value['BOOL']
            elif 'M' in value:
                result[key] = self._dynamodb_to_dict(value['M'])
            elif 'L' in value:
                result[key] = [self._dynamodb_to_dict(v) if isinstance(v, dict) else v for v in value['L']]
        return result


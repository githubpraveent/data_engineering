"""
Scenario B: Real-Time Ingestion from Kafka via Snowpipe Streaming
Python client code to write Kafka events to Snowpipe Streaming
"""

from snowflake.snowpark import Session
from snowflake.ingest import SimpleIngestManager
from snowflake.ingest import StagedFile
from snowflake.ingest.utils import UploadResult
import json
import time
from typing import Dict, Any, List
from confluent_kafka import Consumer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SnowpipeStreamingClient:
    """Client for writing Kafka events to Snowpipe Streaming"""
    
    def __init__(self, snowflake_config: Dict[str, str]):
        """
        Initialize Snowpipe Streaming client
        
        Args:
            snowflake_config: Dictionary with Snowflake connection details
                - account: Snowflake account identifier
                - user: Username
                - password: Password (or use key_pair)
                - warehouse: Warehouse name
                - database: Database name
                - schema: Schema name
                - pipe: Pipe name
        """
        self.config = snowflake_config
        self.session = None
        self.ingest_manager = None
        
    def connect(self):
        """Establish connection to Snowflake"""
        try:
            connection_params = {
                "account": self.config["account"],
                "user": self.config["user"],
                "password": self.config.get("password"),
                "warehouse": self.config.get("warehouse", "WH_TRANS"),
                "database": self.config.get("database", "DEV_RAW"),
                "schema": self.config.get("schema", "BRONZE"),
            }
            
            if self.config.get("key_pair"):
                connection_params["private_key"] = self.config["key_pair"]
            
            self.session = Session.builder.configs(connection_params).create()
            logger.info("Connected to Snowflake successfully")
            
            # Initialize ingest manager for Snowpipe Streaming
            pipe_name = f"{self.config['database']}.{self.config['schema']}.{self.config['pipe']}"
            self.ingest_manager = self.session.create_ingest_manager(pipe_name)
            
        except Exception as e:
            logger.error(f"Failed to connect to Snowflake: {e}")
            raise
    
    def transform_kafka_event(self, kafka_message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Kafka message to Snowflake format
        
        Args:
            kafka_message: Raw Kafka message (dict or JSON string)
            
        Returns:
            Transformed event dictionary
        """
        if isinstance(kafka_message, str):
            kafka_message = json.loads(kafka_message)
        
        # Extract Kafka metadata if available
        topic = kafka_message.get("topic", "unknown")
        partition = kafka_message.get("partition", 0)
        offset = kafka_message.get("offset", 0)
        timestamp = kafka_message.get("timestamp", int(time.time() * 1000))
        
        # Extract event data
        event_data = kafka_message.get("value", kafka_message.get("payload", kafka_message))
        
        # Build Snowflake-compatible event
        snowflake_event = {
            "event_id": event_data.get("event_id", f"{topic}_{partition}_{offset}"),
            "event_timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(timestamp / 1000)),
            "event_type": event_data.get("event_type", "INSERT"),
            "transaction_id": event_data.get("transaction_id"),
            "transaction_timestamp": event_data.get("transaction_timestamp", 
                time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())),
            "store_id": event_data.get("store_id"),
            "register_id": event_data.get("register_id"),
            "customer_id": event_data.get("customer_id"),
            "product_id": event_data.get("product_id"),
            "product_sku": event_data.get("product_sku"),
            "quantity": event_data.get("quantity", 0),
            "unit_price": event_data.get("unit_price", 0),
            "discount_amount": event_data.get("discount_amount", 0),
            "tax_amount": event_data.get("tax_amount", 0),
            "total_amount": event_data.get("total_amount", 0),
            "payment_method": event_data.get("payment_method"),
            "payment_status": event_data.get("payment_status"),
            "kafka_topic": topic,
            "kafka_partition": partition,
            "kafka_offset": offset,
        }
        
        return snowflake_event
    
    def ingest_event(self, event: Dict[str, Any]) -> UploadResult:
        """
        Ingest a single event into Snowpipe Streaming
        
        Args:
            event: Event dictionary
            
        Returns:
            UploadResult
        """
        if not self.ingest_manager:
            raise RuntimeError("Not connected to Snowflake. Call connect() first.")
        
        try:
            # Convert event to JSON
            event_json = json.dumps(event)
            
            # Create staged file (in-memory for streaming)
            staged_file = StagedFile(file_name=f"event_{event['event_id']}.json", 
                                   file_content=event_json.encode('utf-8'))
            
            # Ingest the event
            result = self.ingest_manager.ingest_files([staged_file])
            logger.debug(f"Ingested event {event['event_id']}: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to ingest event {event.get('event_id')}: {e}")
            raise
    
    def ingest_batch(self, events: List[Dict[str, Any]]) -> UploadResult:
        """
        Ingest multiple events in a batch
        
        Args:
            events: List of event dictionaries
            
        Returns:
            UploadResult
        """
        if not self.ingest_manager:
            raise RuntimeError("Not connected to Snowflake. Call connect() first.")
        
        try:
            staged_files = []
            for event in events:
                event_json = json.dumps(event)
                staged_file = StagedFile(
                    file_name=f"batch_{int(time.time())}_{event['event_id']}.json",
                    file_content=event_json.encode('utf-8')
                )
                staged_files.append(staged_file)
            
            result = self.ingest_manager.ingest_files(staged_files)
            logger.info(f"Ingested batch of {len(events)} events: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to ingest batch: {e}")
            raise
    
    def close(self):
        """Close connection"""
        if self.session:
            self.session.close()
            logger.info("Disconnected from Snowflake")


class KafkaToSnowflakeBridge:
    """Bridge between Kafka consumer and Snowpipe Streaming"""
    
    def __init__(self, kafka_config: Dict[str, str], snowflake_config: Dict[str, str]):
        """
        Initialize Kafka-to-Snowflake bridge
        
        Args:
            kafka_config: Kafka consumer configuration
            snowflake_config: Snowflake connection configuration
        """
        self.kafka_config = kafka_config
        self.snowflake_client = SnowpipeStreamingClient(snowflake_config)
        self.consumer = None
        self.batch_size = 100  # Batch events before sending to Snowflake
        self.batch = []
        
    def start(self, topics: List[str]):
        """Start consuming from Kafka and writing to Snowflake"""
        # Connect to Snowflake
        self.snowflake_client.connect()
        
        # Create Kafka consumer
        self.consumer = Consumer(self.kafka_config)
        self.consumer.subscribe(topics)
        
        logger.info(f"Started consuming from Kafka topics: {topics}")
        logger.info("Writing events to Snowflake Snowpipe Streaming...")
        
        try:
            while True:
                msg = self.consumer.poll(timeout=1.0)
                
                if msg is None:
                    # No message, check if we should flush batch
                    if len(self.batch) >= self.batch_size:
                        self._flush_batch()
                    continue
                
                if msg.error():
                    logger.error(f"Kafka error: {msg.error()}")
                    continue
                
                # Parse message
                try:
                    message_value = json.loads(msg.value().decode('utf-8'))
                    kafka_metadata = {
                        "topic": msg.topic(),
                        "partition": msg.partition(),
                        "offset": msg.offset(),
                        "timestamp": msg.timestamp()[1] if msg.timestamp() else int(time.time() * 1000)
                    }
                    message_value.update(kafka_metadata)
                    
                    # Transform to Snowflake format
                    event = self.snowflake_client.transform_kafka_event(message_value)
                    
                    # Add to batch
                    self.batch.append(event)
                    
                    # Flush batch if full
                    if len(self.batch) >= self.batch_size:
                        self._flush_batch()
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse Kafka message: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    continue
                    
        except KeyboardInterrupt:
            logger.info("Stopping consumer...")
        finally:
            # Flush remaining batch
            if self.batch:
                self._flush_batch()
            self.consumer.close()
            self.snowflake_client.close()
    
    def _flush_batch(self):
        """Flush current batch to Snowflake"""
        if not self.batch:
            return
        
        try:
            self.snowflake_client.ingest_batch(self.batch)
            logger.info(f"Flushed batch of {len(self.batch)} events to Snowflake")
            self.batch = []
        except Exception as e:
            logger.error(f"Failed to flush batch: {e}")
            # Optionally: retry logic, dead letter queue, etc.


# Example usage
if __name__ == "__main__":
    # Kafka configuration
    kafka_config = {
        "bootstrap.servers": "localhost:9092",
        "group.id": "snowflake-ingester",
        "auto.offset.reset": "latest",
        "enable.auto.commit": True,
    }
    
    # Snowflake configuration
    snowflake_config = {
        "account": "your_account",
        "user": "your_user",
        "password": "your_password",
        "warehouse": "WH_TRANS",
        "database": "DEV_RAW",
        "schema": "BRONZE",
        "pipe": "pipe_pos_events_streaming",
    }
    
    # Create bridge and start
    bridge = KafkaToSnowflakeBridge(kafka_config, snowflake_config)
    bridge.start(["pos-events", "refund-events"])


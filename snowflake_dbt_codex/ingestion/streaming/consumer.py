import json
import os

from typing import Dict

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "claims.events")


def process_event(event: Dict):
    # Placeholder for processing logic.
    # Write to Snowflake raw table or landing storage.
    _ = event


def run_streaming_consumer():
    # Placeholder for Kafka consumer loop.
    # Replace with confluent-kafka or kafka-python usage.
    sample_event = {"event_type": "claim_created", "claim_id": "C123"}
    process_event(sample_event)

import json
import os

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "claims.events")


def produce_sample_event():
    # Placeholder for producing events to Kafka.
    event = {"event_type": "claim_created", "claim_id": "C123"}
    _ = event

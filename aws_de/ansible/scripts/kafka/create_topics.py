#!/usr/bin/env python3
"""
Script to create Kafka topics on MSK using IAM authentication
"""
import os
import sys
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError
import boto3

def create_kafka_topics():
    bootstrap_servers = os.environ.get('MSK_BOOTSTRAP_SERVERS')
    topic_name = os.environ.get('TOPIC_NAME')
    partitions = int(os.environ.get('PARTITIONS', '3'))
    replication_factor = int(os.environ.get('REPLICATION_FACTOR', '3'))
    aws_region = os.environ.get('AWS_REGION', 'us-east-1')

    if not bootstrap_servers or not topic_name:
        print("ERROR: MSK_BOOTSTRAP_SERVERS and TOPIC_NAME must be set", file=sys.stderr)
        sys.exit(1)

    # Configure Kafka client with IAM authentication
    config = {
        'bootstrap_servers': bootstrap_servers.split(','),
        'security_protocol': 'SASL_SSL',
        'sasl_mechanism': 'AWS_MSK_IAM',
        'sasl_jaas_config': 'software.amazon.msk.auth.iam.IAMLoginModule required;',
        'sasl_client_callback_handler_class': 'software.amazon.msk.auth.iam.IAMClientCallbackHandler',
        'client_id': 'ansible-topic-creator'
    }

    try:
        admin_client = KafkaAdminClient(**config)
        
        topic = NewTopic(
            name=topic_name,
            num_partitions=partitions,
            replication_factor=replication_factor,
            topic_configs={
                'retention.ms': '604800000',  # 7 days
                'compression.type': 'snappy'
            }
        )

        admin_client.create_topics([topic])
        print(f"SUCCESS: Topic {topic_name} created successfully")
        sys.exit(0)

    except TopicAlreadyExistsError:
        print(f"INFO: Topic {topic_name} already exists")
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: Failed to create topic {topic_name}: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    create_kafka_topics()


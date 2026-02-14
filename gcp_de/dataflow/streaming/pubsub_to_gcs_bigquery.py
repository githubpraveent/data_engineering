"""
Streaming Dataflow Pipeline
Consumes messages from Pub/Sub, transforms them, and writes to GCS (raw zone) and BigQuery.
"""

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.io import WriteToBigQuery, WriteToText
from apache_beam.io.gcp.bigquery import BigQueryDisposition
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ParseJson(beam.DoFn):
    """Parse JSON messages from Pub/Sub."""
    
    def process(self, element):
        try:
            message = json.loads(element.decode('utf-8'))
            # Add processing timestamp
            message['processing_timestamp'] = datetime.utcnow().isoformat()
            yield message
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            # Yield error record for dead letter queue
            yield {
                'error': str(e),
                'raw_message': element.decode('utf-8', errors='ignore'),
                'processing_timestamp': datetime.utcnow().isoformat()
            }


class ValidateTransaction(beam.DoFn):
    """Validate transaction records."""
    
    def process(self, element):
        required_fields = ['transaction_id', 'customer_id', 'product_id', 'amount', 'timestamp']
        
        if all(field in element for field in required_fields):
            # Additional validation
            if element.get('amount', 0) >= 0:
                yield element
            else:
                logger.warning(f"Invalid amount in transaction: {element.get('transaction_id')}")
        else:
            logger.warning(f"Missing required fields in transaction: {element}")


class TransformTransaction(beam.DoFn):
    """Transform transaction data for BigQuery."""
    
    def process(self, element):
        try:
            transformed = {
                'transaction_id': element.get('transaction_id'),
                'customer_id': element.get('customer_id'),
                'product_id': element.get('product_id'),
                'store_id': element.get('store_id'),
                'transaction_timestamp': element.get('timestamp'),
                'quantity': element.get('quantity', 1),
                'unit_price': element.get('unit_price', element.get('amount', 0)),
                'total_amount': element.get('amount', 0),
                'payment_method': element.get('payment_method', 'UNKNOWN'),
                'load_timestamp': datetime.utcnow().isoformat(),
            }
            yield transformed
        except Exception as e:
            logger.error(f"Error transforming transaction: {e}")
            yield element


def run_streaming_pipeline(argv=None):
    """Main function to run the streaming pipeline."""
    
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--input_subscription',
        required=True,
        help='Pub/Sub subscription to read from'
    )
    parser.add_argument(
        '--output_gcs',
        required=True,
        help='GCS path for raw data output (gs://bucket/path)'
    )
    parser.add_argument(
        '--output_table',
        required=True,
        help='BigQuery table in format project:dataset.table'
    )
    parser.add_argument(
        '--dead_letter_table',
        required=False,
        help='BigQuery table for error records'
    )
    parser.add_argument(
        '--window_size',
        default=300,  # 5 minutes
        type=int,
        help='Window size in seconds'
    )
    
    known_args, pipeline_args = parser.parse_known_args(argv)
    
    # Pipeline options
    pipeline_options = PipelineOptions(pipeline_args)
    pipeline_options.view_as(beam.options.pipeline_options.StandardOptions).streaming = True
    
    # Build pipeline
    with beam.Pipeline(options=pipeline_options) as pipeline:
        # Read from Pub/Sub
        messages = (
            pipeline
            | 'Read from Pub/Sub' >> beam.io.ReadFromPubSub(
                subscription=known_args.input_subscription
            )
        )
        
        # Parse JSON
        parsed = (
            messages
            | 'Parse JSON' >> beam.ParDo(ParseJson())
        )
        
        # Split into valid and error records
        valid_records = (
            parsed
            | 'Filter Errors' >> beam.Filter(lambda x: 'error' not in x)
            | 'Validate Transactions' >> beam.ParDo(ValidateTransaction())
        )
        
        error_records = (
            parsed
            | 'Filter Valid' >> beam.Filter(lambda x: 'error' in x)
        )
        
        # Write valid records to GCS (raw zone) with windowing
        windowed_records = (
            valid_records
            | 'Window' >> beam.WindowInto(
                beam.window.FixedWindows(known_args.window_size)
            )
        )
        
        # Write to GCS as JSON
        (
            windowed_records
            | 'Format for GCS' >> beam.Map(lambda x: json.dumps(x))
            | 'Write to GCS' >> WriteToText(
                file_path_prefix=known_args.output_gcs,
                file_name_suffix='.json',
                num_shards=1
            )
        )
        
        # Transform for BigQuery
        transformed = (
            valid_records
            | 'Transform for BigQuery' >> beam.ParDo(TransformTransaction())
        )
        
        # Write to BigQuery
        (
            transformed
            | 'Write to BigQuery' >> WriteToBigQuery(
                table=known_args.output_table,
                write_disposition=BigQueryDisposition.WRITE_APPEND,
                create_disposition=BigQueryDisposition.CREATE_IF_NEEDED,
                schema='transaction_id:STRING,customer_id:STRING,product_id:STRING,'
                       'store_id:STRING,transaction_timestamp:TIMESTAMP,quantity:INTEGER,'
                       'unit_price:FLOAT,total_amount:FLOAT,payment_method:STRING,load_timestamp:TIMESTAMP'
            )
        )
        
        # Write error records to dead letter table if specified
        if known_args.dead_letter_table:
            (
                error_records
                | 'Write Errors to BigQuery' >> WriteToBigQuery(
                    table=known_args.dead_letter_table,
                    write_disposition=BigQueryDisposition.WRITE_APPEND,
                    create_disposition=BigQueryDisposition.CREATE_IF_NEEDED,
                    schema='error:STRING,raw_message:STRING,processing_timestamp:TIMESTAMP'
                )
            )


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run_streaming_pipeline()


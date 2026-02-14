"""
Batch Dataflow Pipeline
Reads data from GCS, applies transformations, and writes to GCS (staging/curated) and BigQuery.
"""

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.io import ReadFromText, WriteToText
from apache_beam.io.gcp.bigquery import WriteToBigQuery, BigQueryDisposition
import json
import csv
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ParseCSV(beam.DoFn):
    """Parse CSV files."""
    
    def __init__(self, delimiter=','):
        self.delimiter = delimiter
    
    def process(self, element):
        try:
            reader = csv.DictReader(element.splitlines(), delimiter=self.delimiter)
            for row in reader:
                yield dict(row)
        except Exception as e:
            logger.error(f"Error parsing CSV: {e}")
            yield {'error': str(e), 'raw_line': element}


class ParseJSON(beam.DoFn):
    """Parse JSON files."""
    
    def process(self, element):
        try:
            data = json.loads(element)
            if isinstance(data, list):
                for item in data:
                    yield item
            else:
                yield data
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON: {e}")
            yield {'error': str(e), 'raw_line': element}


class CleanData(beam.DoFn):
    """Clean and standardize data."""
    
    def process(self, element):
        if 'error' in element:
            yield element
            return
        
        try:
            cleaned = {}
            for key, value in element.items():
                # Normalize keys (lowercase, replace spaces with underscores)
                normalized_key = key.lower().replace(' ', '_').strip()
                
                # Clean values
                if value is None or value == '':
                    cleaned[normalized_key] = None
                elif isinstance(value, str):
                    cleaned[normalized_key] = value.strip()
                else:
                    cleaned[normalized_key] = value
            
            # Add metadata
            cleaned['load_timestamp'] = datetime.utcnow().isoformat()
            cleaned['source_file'] = element.get('source_file', 'unknown')
            
            yield cleaned
        except Exception as e:
            logger.error(f"Error cleaning data: {e}")
            yield {'error': str(e), 'raw_record': element}


class ValidateSchema(beam.DoFn):
    """Validate data against expected schema."""
    
    def __init__(self, required_fields):
        self.required_fields = required_fields
    
    def process(self, element):
        if 'error' in element:
            yield element
            return
        
        missing_fields = [field for field in self.required_fields if field not in element]
        
        if missing_fields:
            logger.warning(f"Missing required fields: {missing_fields}")
            element['validation_errors'] = f"Missing fields: {', '.join(missing_fields)}"
        
        yield element


class TransformTransactions(beam.DoFn):
    """Transform transaction data for staging/curated zones."""
    
    def process(self, element):
        if 'error' in element:
            yield element
            return
        
        try:
            transformed = {
                'transaction_id': element.get('transaction_id') or element.get('id'),
                'customer_id': element.get('customer_id'),
                'product_id': element.get('product_id'),
                'store_id': element.get('store_id'),
                'transaction_timestamp': self._parse_timestamp(
                    element.get('timestamp') or 
                    element.get('transaction_timestamp') or
                    element.get('date')
                ),
                'quantity': self._safe_int(element.get('quantity', 1)),
                'unit_price': self._safe_float(element.get('unit_price') or element.get('price', 0)),
                'total_amount': self._safe_float(element.get('total_amount') or element.get('amount', 0)),
                'payment_method': element.get('payment_method', 'UNKNOWN'),
                'load_timestamp': datetime.utcnow().isoformat(),
            }
            yield transformed
        except Exception as e:
            logger.error(f"Error transforming transaction: {e}")
            yield {'error': str(e), 'raw_record': element}
    
    def _parse_timestamp(self, timestamp_str):
        """Parse various timestamp formats."""
        if not timestamp_str:
            return datetime.utcnow().isoformat()
        
        # Try common formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%d',
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(str(timestamp_str), fmt)
                return dt.isoformat()
            except ValueError:
                continue
        
        return timestamp_str
    
    def _safe_int(self, value):
        """Safely convert to integer."""
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return 0
    
    def _safe_float(self, value):
        """Safely convert to float."""
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0


def run_batch_pipeline(argv=None):
    """Main function to run the batch pipeline."""
    
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--input',
        required=True,
        help='GCS input path (gs://bucket/path)'
    )
    parser.add_argument(
        '--output_gcs',
        required=False,
        help='GCS output path for transformed data'
    )
    parser.add_argument(
        '--output_table',
        required=False,
        help='BigQuery table in format project:dataset.table'
    )
    parser.add_argument(
        '--input_format',
        default='json',
        choices=['json', 'csv'],
        help='Input file format'
    )
    parser.add_argument(
        '--required_fields',
        default='transaction_id,customer_id,product_id',
        help='Comma-separated list of required fields'
    )
    
    known_args, pipeline_args = parser.parse_known_args(argv)
    
    # Pipeline options
    pipeline_options = PipelineOptions(pipeline_args)
    
    required_fields_list = known_args.required_fields.split(',')
    
    # Build pipeline
    with beam.Pipeline(options=pipeline_options) as pipeline:
        # Read from GCS
        if known_args.input_format == 'json':
            records = (
                pipeline
                | 'Read from GCS' >> ReadFromText(known_args.input)
                | 'Parse JSON' >> beam.ParDo(ParseJSON())
            )
        else:  # CSV
            records = (
                pipeline
                | 'Read from GCS' >> ReadFromText(known_args.input)
                | 'Parse CSV' >> beam.ParDo(ParseCSV())
            )
        
        # Clean data
        cleaned = (
            records
            | 'Clean Data' >> beam.ParDo(CleanData())
        )
        
        # Validate schema
        validated = (
            cleaned
            | 'Validate Schema' >> beam.ParDo(ValidateSchema(required_fields_list))
        )
        
        # Split valid and error records
        valid_records = (
            validated
            | 'Filter Valid' >> beam.Filter(lambda x: 'error' not in x and 'validation_errors' not in x)
        )
        
        error_records = (
            validated
            | 'Filter Errors' >> beam.Filter(lambda x: 'error' in x or 'validation_errors' in x)
        )
        
        # Transform for target schema
        transformed = (
            valid_records
            | 'Transform Data' >> beam.ParDo(TransformTransactions())
        )
        
        # Write to GCS if specified
        if known_args.output_gcs:
            (
                transformed
                | 'Format for GCS' >> beam.Map(lambda x: json.dumps(x))
                | 'Write to GCS' >> WriteToText(
                    file_path_prefix=known_args.output_gcs,
                    file_name_suffix='.json',
                    num_shards=1
                )
            )
        
        # Write to BigQuery if specified
        if known_args.output_table:
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


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run_batch_pipeline()


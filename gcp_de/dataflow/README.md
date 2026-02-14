# Dataflow Pipelines

This directory contains Apache Beam pipelines for both streaming and batch data processing.

## Structure

- `streaming/`: Streaming pipelines that consume from Pub/Sub
- `batch/`: Batch pipelines that process files from GCS
- `requirements.txt`: Python dependencies
- `setup.py`: Package setup for Dataflow

## Deployment

### Build and Deploy Templates

1. **Build the pipeline package:**
   ```bash
   python setup.py sdist
   ```

2. **Deploy streaming pipeline template:**
   ```bash
   python streaming/pubsub_to_gcs_bigquery.py \
     --runner DataflowRunner \
     --project YOUR_PROJECT_ID \
     --region us-central1 \
     --temp_location gs://YOUR_BUCKET/temp \
     --staging_location gs://YOUR_BUCKET/staging \
     --template_location gs://YOUR_BUCKET/templates/streaming_pipeline_template \
     --input_subscription projects/YOUR_PROJECT/subscriptions/retail-transactions-dataflow-dev \
     --output_gcs gs://YOUR_BUCKET/raw/transactions/ \
     --output_table YOUR_PROJECT:staging_dev.transactions \
     --window_size 300
   ```

3. **Deploy batch pipeline template:**
   ```bash
   python batch/gcs_transform_pipeline.py \
     --runner DataflowRunner \
     --project YOUR_PROJECT_ID \
     --region us-central1 \
     --temp_location gs://YOUR_BUCKET/temp \
     --staging_location gs://YOUR_BUCKET/staging \
     --template_location gs://YOUR_BUCKET/templates/batch_transform_template \
     --input gs://YOUR_BUCKET/raw/transactions/ \
     --output_gcs gs://YOUR_BUCKET/staging/transactions/ \
     --output_table YOUR_PROJECT:staging_dev.transactions_staging \
     --input_format json
   ```

## Running Locally

For testing, you can run pipelines locally:

```bash
python streaming/pubsub_to_gcs_bigquery.py \
  --runner DirectRunner \
  --input_subscription projects/YOUR_PROJECT/subscriptions/test-subscription \
  --output_gcs /tmp/output \
  --output_table YOUR_PROJECT:test_dataset.test_table
```

## Pipeline Parameters

### Streaming Pipeline
- `--input_subscription`: Pub/Sub subscription to read from
- `--output_gcs`: GCS path for raw data output
- `--output_table`: BigQuery destination table
- `--dead_letter_table`: (Optional) BigQuery table for error records
- `--window_size`: Window size in seconds (default: 300)

### Batch Pipeline
- `--input`: GCS input path
- `--output_gcs`: (Optional) GCS output path
- `--output_table`: (Optional) BigQuery destination table
- `--input_format`: Input format (json or csv)
- `--required_fields`: Comma-separated required fields


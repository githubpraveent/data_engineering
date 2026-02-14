# Data Pipeline

This directory contains the data pipeline code for ingesting, transforming, and aggregating data in Google Cloud Bigtable.

## Structure

```
pipelines/
├── ingestion/          # Data ingestion scripts
│   ├── batch_ingestion.py
│   └── stream_ingestion.py (optional)
├── transformation/     # Data transformation logic
│   └── transform.py
├── quality/            # Data quality checks
│   └── quality_checks.py
├── aggregation/        # Aggregation logic
│   └── aggregator.py
└── utils/              # Utility functions
    ├── bigtable_client.py
    └── retry_handler.py
```

## Usage

### Batch Ingestion

```bash
# Ingest from CSV file
python pipelines/ingestion/batch_ingestion.py \
  --source data/sample_events.csv \
  --format csv \
  --project-id your-project-id \
  --instance-id your-instance-id \
  --batch-size 100

# Ingest from JSON file
python pipelines/ingestion/batch_ingestion.py \
  --source data/events.json \
  --format json \
  --project-id your-project-id \
  --instance-id your-instance-id

# Disable quality checks
python pipelines/ingestion/batch_ingestion.py \
  --source data/sample_events.csv \
  --no-quality-checks \
  --project-id your-project-id \
  --instance-id your-instance-id
```

### Aggregation

```bash
# Run daily aggregation job
python pipelines/aggregation/aggregator.py \
  --project-id your-project-id \
  --instance-id your-instance-id \
  --date 2024-01-15

# Use defaults (aggregates yesterday's data)
python pipelines/aggregation/aggregator.py \
  --project-id your-project-id \
  --instance-id your-instance-id
```

### Data Quality Checks

The quality checker validates:
- Required fields presence
- Schema validation (types)
- Missing or null values
- Duplicate detection
- Data range checks (e.g., future timestamps)

### Bigtable Client

```python
from pipelines.utils.bigtable_client import BigTableClient

# Initialize client
client = BigTableClient(
    project_id="your-project-id",
    instance_id="your-instance-id"
)

# Write an event
client.write_event(
    user_id="user123",
    event_id="event456",
    event_data={"event_type": "click", "page": "/home"}
)

# Get user events
events = client.get_user_events(
    user_id="user123",
    start_time=datetime(2024, 1, 15),
    end_time=datetime(2024, 1, 16),
    limit=100
)

# Write aggregate
client.write_aggregate(
    dimension="user",
    dimension_value="user123",
    date=datetime(2024, 1, 15),
    stats={"total_events": 100, "unique_songs": 25}
)

# Get daily aggregates
aggregates = client.get_daily_aggregates(
    dimension="user",
    dimension_value="user123",
    date=datetime(2024, 1, 15)
)
```

## Configuration

Set environment variables:
```bash
export GCP_PROJECT_ID="your-project-id"
export BIGTABLE_INSTANCE="your-instance-id"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
```

## Testing

```bash
# Run unit tests
pytest tests/unit/ -v

# Run integration tests (requires GCP credentials)
pytest tests/integration/ -v -m integration

# Run with coverage
pytest tests/ --cov=pipelines --cov-report=html
```

## Error Handling

The pipeline includes retry logic with exponential backoff for:
- ServiceUnavailable errors
- InternalServerError
- DeadlineExceeded
- TooManyRequests
- Network/Connection errors

## Performance Considerations

- Use batch writes for better throughput
- Adjust batch size based on event size (default: 100)
- Monitor Bigtable quotas and adjust accordingly
- Consider using streaming ingestion for real-time data

# Tests

This directory contains test scripts for unit, integration, and data quality testing.

## Structure

- `unit/`: Unit tests for pipeline components
- `integration/`: Integration tests requiring GCP resources
- `data_quality/`: Data quality validation tests

## Running Tests

### Unit Tests

```bash
cd tests/unit
python -m pytest test_dataflow_pipelines.py -v
```

### Integration Tests

Requires GCP credentials:

```bash
export GCP_PROJECT=your-project-id
export ENVIRONMENT=dev
gcloud auth application-default login

cd tests/integration
python -m pytest test_pipeline_integration.py -v
```

### Data Quality Tests

```bash
export GCP_PROJECT=your-project-id
export ENVIRONMENT=dev
gcloud auth application-default login

cd tests/data_quality
python -m pytest test_data_quality.py -v
```

## Test Coverage

### Unit Tests
- JSON/CSV parsing
- Data validation
- Data transformation
- Data cleaning

### Integration Tests
- BigQuery table existence
- GCS bucket existence
- Pub/Sub topic existence
- Referential integrity
- Data quality checks

### Data Quality Tests
- Null checks
- Data freshness
- Negative value checks
- Consistency checks
- Completeness checks

## CI/CD Integration

Tests are automatically run in GitHub Actions workflows (see `ci-cd/.github/workflows/tests.yml`).


# Test Suite

This directory contains test scripts for validating the data pipeline.

## Structure

```
tests/
├── kafka/              # Kafka topic and message validation tests
├── glue/               # Glue ETL transformation tests
├── redshift/           # Redshift data quality tests
├── integration/        # End-to-end integration tests
└── requirements.txt   # Python dependencies
```

## Running Tests

### All Tests
```bash
pytest tests/ -v
```

### Specific Test Suite
```bash
# Kafka tests
pytest tests/kafka/ -v

# Glue tests
pytest tests/glue/ -v

# Redshift tests
pytest tests/redshift/ -v

# Integration tests
pytest tests/integration/ -v
```

### With Coverage
```bash
pytest tests/ --cov=. --cov-report=html
```

## Test Categories

### Kafka Tests
- Topic naming convention validation
- Message schema validation
- Operation type validation

### Glue Tests
- Data transformation logic
- Data cleaning functions
- Validation rules
- Deduplication logic

### Redshift Tests
- SCD Type 1/2 behavior
- Referential integrity
- Data quality checks
- Surrogate key uniqueness

### Integration Tests
- End-to-end data flow
- Component connectivity
- Schema existence
- Job availability

## Environment Variables

Set these environment variables for tests:

```bash
export AWS_REGION=us-east-1
export MSK_BOOTSTRAP_SERVERS=<msk-endpoint>
export REDSHIFT_HOST=<redshift-endpoint>
export REDSHIFT_PORT=5439
export REDSHIFT_DATABASE=retail_dw
export REDSHIFT_USER=<username>
export REDSHIFT_PASSWORD=<password>
export S3_DATALAKE_BUCKET=<bucket-name>
export ENVIRONMENT=dev
```

## CI/CD Integration

Tests run automatically in GitHub Actions on:
- Pull requests
- Pushes to main/qa/dev branches
- Manual workflow dispatch

See `.github/workflows/run-tests.yml` for details.


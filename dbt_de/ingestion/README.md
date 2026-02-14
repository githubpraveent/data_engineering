# Data Ingestion Layer

This directory contains scripts and utilities for ingesting data from source systems into the data lake bronze layer.

## Structure

```
ingestion/
├── scripts/           # Ingestion scripts
│   ├── ingest_orders.py
│   ├── ingest_customers_cdc.py
│   └── ...
└── connectors/       # Source system connectors
```

## Ingestion Types

### Batch Ingestion
- Scheduled extraction from source systems
- Examples: `ingest_orders.py`, `ingest_products.py`
- Runs on schedule (daily, hourly, etc.)

### CDC (Change Data Capture)
- Real-time or near-real-time change capture
- Examples: `ingest_customers_cdc.py`
- Captures INSERT, UPDATE, DELETE events

## Usage

### Batch Ingestion
```bash
python ingestion/scripts/ingest_orders.py \
    --start-date 2024-01-01 \
    --end-date 2024-01-01 \
    --output-path s3://data-lake/bronze/orders
```

### CDC Ingestion
```bash
python ingestion/scripts/ingest_customers_cdc.py \
    --since 2024-01-01T00:00:00 \
    --output-path s3://data-lake/bronze/customers/cdc
```

## Integration with Airflow

These scripts are called by Airflow DAGs in `airflow/dags/data_ingestion.py`.

## Source System Connectors

To add a new source system:

1. Create a connector module in `connectors/`
2. Implement connection, extraction, and transformation logic
3. Create an ingestion script that uses the connector
4. Add to Airflow DAG


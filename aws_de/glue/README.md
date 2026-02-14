# AWS Glue ETL Jobs

This directory contains AWS Glue ETL jobs for streaming and batch processing.

## Structure

```
glue/
├── streaming/          # Real-time streaming jobs (MSK → S3)
│   ├── customer_streaming.py
│   └── order_streaming.py
├── batch/             # Batch transformation jobs
│   ├── landing_to_staging.py
│   └── staging_to_curated.py
└── tests/             # Unit tests for ETL jobs
```

## Streaming Jobs

### Customer Streaming
- **Purpose**: Consumes customer CDC events from MSK and writes to S3 landing zone
- **Input**: Kafka topic `retail.customer.cdc`
- **Output**: S3 path `s3://retail-datalake-{env}/landing/customer/`
- **Format**: Parquet, partitioned by year/month/day/hour

### Order Streaming
- **Purpose**: Consumes order CDC events from MSK and writes to S3 landing zone
- **Input**: Kafka topic `retail.order.cdc`
- **Output**: S3 path `s3://retail-datalake-{env}/landing/order/`
- **Format**: Parquet, partitioned by year/month/day/hour

## Batch Jobs

### Landing to Staging
- **Purpose**: Transforms raw CDC events to cleaned staging data
- **Input**: S3 landing zone
- **Output**: S3 staging zone
- **Operations**:
  - Data validation
  - Data cleaning (trim, normalize)
  - Deduplication
  - Quality flagging

### Staging to Curated
- **Purpose**: Creates business-ready star schema dimensions and facts
- **Input**: S3 staging zone
- **Output**: S3 curated zone
- **Outputs**:
  - Customer dimension
  - Date dimension
  - Sales fact table

## Deployment

Jobs are deployed via Terraform (see `terraform/modules/glue/`) and CI/CD pipeline.

## Testing

Run unit tests:
```bash
python -m pytest glue/tests/
```

## Monitoring

- CloudWatch Logs: `/aws-glue/jobs/{job-name}`
- CloudWatch Metrics: Job success/failure, duration
- Glue Job Dashboard: AWS Console


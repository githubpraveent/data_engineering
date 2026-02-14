# Architecture Documentation

## Overview

This project implements a production-ready data engineering pipeline using Google Cloud Bigtable for storing and querying event data.

## Components

### 1. Infrastructure (Terraform)

**Purpose**: Infrastructure as Code for GCP resources

**Key Resources**:
- Google Bigtable instance and tables
- VPC network and subnets
- Firewall rules
- Service accounts with IAM roles

**Structure**:
```
terraform/
├── modules/           # Reusable modules
│   ├── bigtable/     # Bigtable resources
│   ├── networking/   # VPC and networking
│   └── service-accounts/  # IAM
└── environments/     # Environment-specific configs
    ├── dev/
    ├── staging/
    └── production/
```

### 2. Configuration Management (Ansible)

**Purpose**: Idempotent configuration of application servers

**Roles**:
- `python-runtime`: Installs Python and dependencies
- `bigtable-client`: Sets up Bigtable client libraries
- `pipeline-service`: Deploys pipeline as system service

### 3. CI/CD (GitHub Actions)

**Workflows**:
- `terraform-validate.yml`: Validates Terraform on PR
- `terraform-apply.yml`: Applies Terraform changes
- `pipeline-tests.yml`: Runs tests and linting
- `promote-staging-to-production.yml`: Manual promotion workflow

**Features**:
- Automated testing on pull requests
- Manual approval for production
- Terraform state management
- Integration with Ansible

### 4. Data Pipeline

**Components**:

#### Ingestion
- **Batch Ingestion**: Reads CSV/JSON files and loads into Bigtable
- **Stream Ingestion**: (Optional) Real-time streaming via Pub/Sub

#### Transformation
- Field normalization (camelCase → snake_case)
- Data enrichment (timestamps, metadata)
- Value cleaning and type conversion

#### Quality Checks
- Schema validation
- Required field checks
- Duplicate detection
- Data range validation

#### Aggregation
- Daily aggregates by dimension (user, song, etc.)
- Hourly aggregates
- Weekly rollups

### 5. Data Model

#### Fact Table (`events_fact`)
Row Key Format: `{user_id}#{timestamp_reversed}#{event_id}`

Column Families:
- `event_data`: Event attributes (event_type, page_url, etc.)
- `metadata`: Processing metadata (user_id, event_id, timestamp)
- `quality`: Quality check results

#### Aggregate Table (`events_aggregate`)
Row Key Format: `{dimension}#{dimension_value}#{date}`

Column Families:
- `daily_stats`: Daily aggregations
- `hourly_stats`: Hourly aggregations
- `weekly_stats`: Weekly aggregations
- `metadata`: Aggregate metadata

### 6. Query Patterns

#### User Events
- Scan by user_id prefix
- Filter by time range
- Limit results

#### Aggregates
- Direct lookup by dimension + date
- Range scans for multiple dates

## Data Flow

```
Source Data (CSV/JSON/Pub/Sub)
    ↓
Batch Ingestion Script
    ↓
Data Quality Checks
    ↓
Transformation & Enrichment
    ↓
Bigtable Fact Table
    ↓
Aggregation Job (Daily/Weekly)
    ↓
Bigtable Aggregate Table
    ↓
Query APIs / Analytics
```

## Security

- Service accounts with least privilege
- Secrets managed via GitHub Secrets
- Network isolation via VPC
- Encryption at rest (Bigtable default)
- Encryption in transit (TLS)

## Monitoring

- Cloud Logging for all operations
- Cloud Monitoring for metrics
- Slack alerts for quality failures
- Error tracking and retry logic

## Scalability

- Bigtable scales horizontally
- Batch processing for large volumes
- Parallel aggregation jobs
- Efficient row key design for scans

## Deployment

1. **Infrastructure**: Terraform applies resources
2. **Configuration**: Ansible configures servers
3. **Pipeline**: Python scripts run via cron/systemd
4. **Monitoring**: Alerts configured automatically

## Performance Considerations

- Batch writes for better throughput
- Appropriate row key design for access patterns
- Column family organization for queries
- Efficient time-range filtering

## Error Handling

- Retry logic with exponential backoff
- Dead letter queues for failed events
- Comprehensive logging
- Alerting on failures

## Future Enhancements

- Real-time streaming pipeline
- Machine learning features
- Advanced analytics
- Multi-region replication
- Data retention policies

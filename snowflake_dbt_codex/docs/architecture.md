# Architecture Overview

## Goals
- Support batch and real-time ingestion for healthcare insurance and claims data
- Provide a Snowflake-based warehouse with dbt transformations and tests
- Orchestrate workflows with Airflow, including monitoring and alerting hooks
- Enforce data quality checks and maintain observability across the pipeline
- Publish curated data marts for Databricks reporting

## Logical Architecture
- Sources
- CSV and JSON files in landing storage
- SQL Server for operational claims and member data
- Kafka topics for real-time claims events

- Ingestion
- Batch extractors load files and SQL Server data into Snowflake staging
- Streaming consumers write Kafka events into Snowflake raw tables or landing storage

- Transformation
- dbt models build staging, intermediate, and mart layers
- Tests enforce schema integrity, uniqueness, and relationships

- Serving
- Curated marts exported to Databricks via external stage or file-based exchange
- BI and analytics consume Databricks tables

## Physical Components
- Snowflake
- Warehousing, storage, and secure data sharing
- Schemas: `raw`, `staging`, `intermediate`, `marts`

- Airflow
- DAGs for batch ingest, dbt transformations, validation, and publish
- Separate DAG for streaming ingest monitoring and backfill

- Kafka
- Topics for real-time claims events, member updates, and provider changes

- Quality
- Python-based checks and dbt tests
- Rule configs in `quality/rules/`

- Observability
- Structured logging in Airflow tasks and ingestion scripts
- Metrics hooks for SLA tracking
## Data Flow Summary
1. Batch ingest
1. Extract from SQL Server and file drops
1. Load to Snowflake `raw` schema

2. Streaming ingest
1. Kafka consumers ingest events to `raw` or landing storage
1. Micro-batch upserts into `staging`

3. Transformation
1. dbt staging models standardize types and keys
1. dbt intermediate models enrich and deduplicate
1. dbt marts provide analytics-ready datasets

4. Data quality
1. Python checks validate row counts, referential integrity, and completeness
1. dbt tests verify schemas and constraints

5. Publish
1. Export curated marts to Databricks-friendly storage
1. Databricks reads the curated datasets

## Security and Compliance
- Least-privilege access via Snowflake roles
- PII handling with masking policies and secure views
- Encryption at rest and in transit
- Audit logging for data access and transformations

## SLAs and Monitoring
- Batch SLA targets defined per DAG
- Streaming lag monitoring on Kafka topics
- Alerts on failed dbt tests or quality checks

## Deployment Notes
- Local dev uses Docker Compose and environment variables
- Production deployment should use managed Kafka, Airflow, and Snowflake
- CI pipeline should include dbt compile, dbt test, and unit tests

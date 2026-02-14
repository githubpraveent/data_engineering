# Healthcare Insurance & Claims Data Pipeline (Snowflake + dbt + Airflow + Kafka)

This repository provides a scalable, modular blueprint for batch and streaming data pipelines for healthcare insurance and claims analytics. It is designed for local development with Docker and can be adapted to production cloud environments.

## What This Includes
- End-to-end architecture and data model documentation
- Airflow DAG scaffolding for batch and streaming workflows
- dbt project structure with staging, intermediate, and marts models
- Ingestion scripts for CSV/JSON files and SQL Server
- Streaming stubs using Kafka for real-time event ingestion
- Data quality checks and validation rules
- Observability hooks and logging configuration
- CI placeholders for future automation

## High-Level Flow
- Batch sources: CSV, JSON, SQL Server
- Streaming sources: Kafka topics with claims events
- Warehouse: Snowflake
- Transformations: dbt
- Reporting target: Databricks (via curated export)

## Local Development
1. Review `docs/architecture.md` for the design and operational flow.
2. Use `docker-compose.yml` to bring up Airflow, Kafka, and supporting services.
3. Configure environment variables for Snowflake, SQL Server, and Kafka.
4. Run Airflow DAGs to execute batch loads, dbt transformations, quality checks, and export to Databricks.

## Key Paths
- `docs/architecture.md`
- `docs/data_model.md`
- `airflow/dags/`
- `dbt/`
- `ingestion/`
- `quality/`
- `observability/`

## Notes
- Credentials and secrets are expected to be provided via environment variables.
- This is a design-first, production-ready skeleton. Fill in connection details and cloud-specific resources as needed.

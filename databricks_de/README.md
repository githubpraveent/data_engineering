# Retail Data Lakehouse on Databricks

A scalable, future-proof retail data lakehouse built on Databricks, using Delta Lake, Unity Catalog, and Apache Airflow for orchestration.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        INGESTION LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│  Batch Sources:               Streaming Sources:                │
│  - POS Systems                - Kafka Event Streams             │
│  - Inventory DB               - CDC from Source DBs             │
│  - Orders DB                  - Real-time Transactions          │
└────────────┬──────────────────────────┬─────────────────────────┘
             │                          │
             ▼                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DELTA LAKE STORAGE LAYER                      │
│                      (Medallion Architecture)                    │
├─────────────────────────────────────────────────────────────────┤
│  BRONZE LAYER: Raw/Ingested Data                                │
│  - Raw JSON/Parquet from sources                                │
│  - Streaming CDC feed                                           │
│  - Full historical data                                         │
│                                                                  │
│  SILVER LAYER: Cleaned/Refined Data                             │
│  - Deduplicated records                                         │
│  - Validated schemas                                            │
│  - Canonical staging tables                                     │
│  - Dimension-style data                                         │
│                                                                  │
│  GOLD LAYER: Business-Level Tables                              │
│  - Fact Tables (Sales, Orders, Transactions)                    │
│  - Dimension Tables (Customer, Product, Store, Date)            │
│  - Aggregated Summary Tables                                    │
│  - Data Marts for BI                                            │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  SERVING / ANALYTICAL LAYER                      │
├─────────────────────────────────────────────────────────────────┤
│  - Databricks SQL Warehouses                                    │
│  - BI Tools (Tableau, Power BI, etc.)                           │
│  - Reporting Dashboards                                         │
│  - Delta Sharing (External Partners)                            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       ORCHESTRATION                              │
│                    Apache Airflow DAGs                           │
├─────────────────────────────────────────────────────────────────┤
│  - Ingestion Jobs (Batch + Streaming)                           │
│  - Transformation Jobs (Bronze → Silver → Gold)                 │
│  - Data Quality Checks                                          │
│  - Alerting & Retry Logic                                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      GOVERNANCE & METADATA                       │
│                      Unity Catalog                               │
├─────────────────────────────────────────────────────────────────┤
│  - Table-level Permissions                                      │
│  - Data Lineage Tracking                                        │
│  - Audit Logs                                                   │
│  - Schema Evolution Management                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
.
├── README.md
├── architecture.md                 # Detailed architecture documentation
├── runbook.md                     # Operational runbook
├── .github/
│   └── workflows/                 # CI/CD pipelines
│       ├── deploy-dev.yml
│       ├── deploy-qa.yml
│       └── deploy-prod.yml
├── databricks/
│   ├── notebooks/
│   │   ├── ingestion/
│   │   │   ├── batch/
│   │   │   │   ├── ingest_orders.py
│   │   │   │   ├── ingest_customers.py
│   │   │   │   └── ingest_inventory.py
│   │   │   └── streaming/
│   │   │       └── stream_sales_transactions.py
│   │   ├── transformation/
│   │   │   ├── bronze_to_silver/
│   │   │   │   ├── clean_orders.py
│   │   │   │   ├── clean_customers.py
│   │   │   │   └── clean_inventory.py
│   │   │   └── silver_to_gold/
│   │   │       ├── build_fact_sales.py
│   │   │       ├── build_dim_customer.py
│   │   │       ├── build_dim_product.py
│   │   │       ├── build_dim_store.py
│   │   │       └── build_dim_date.py
│   │   └── utilities/
│   │       ├── schema_definitions.py
│   │       ├── data_quality_checks.py
│   │       └── common_functions.py
│   ├── jobs/
│   │   └── job_definitions.json    # Databricks job definitions
│   └── sql/
│       └── gold_layer_queries.sql  # Sample SQL for Gold layer
├── airflow/
│   ├── dags/
│   │   ├── ingestion_dag.py
│   │   ├── transformation_dag.py
│   │   └── data_quality_dag.py
│   ├── config/
│   │   └── airflow.cfg
│   └── requirements.txt
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── environments/
│       ├── dev.tfvars
│       ├── qa.tfvars
│       └── prod.tfvars
├── tests/
│   ├── unit/
│   │   └── test_transformations.py
│   └── data_quality/
│       └── test_data_quality.py
├── scripts/
│   ├── deploy_notebooks.sh
│   └── setup_unity_catalog.sh
└── governance/
    └── unity_catalog_grants.sql    # Unity Catalog permissions
```

## Features

- **Medallion Architecture**: Bronze (raw), Silver (cleaned), Gold (curated) data layers
- **Batch & Streaming**: Support for both batch and real-time data ingestion
- **Delta Lake**: ACID transactions, schema enforcement, time travel
- **Unity Catalog**: Data governance, lineage, and access control
- **Airflow Orchestration**: Automated pipeline execution with retries and alerts
- **SCD Support**: Type 1 and Type 2 Slowly Changing Dimensions
- **CI/CD**: Automated deployment across Dev → QA → Prod environments
- **Data Quality**: Automated quality checks and validation
- **IaC**: Terraform-based infrastructure provisioning

## Quick Start

### Prerequisites

- Databricks account with workspace access
- Apache Airflow instance (managed or self-hosted)
- Python 3.8+
- Terraform 1.0+
- Databricks CLI configured

### Setup

1. **Configure Databricks CLI**:
   ```bash
   databricks configure --token
   ```

2. **Deploy Infrastructure**:
   ```bash
   cd terraform
   terraform init
   terraform plan -var-file=environments/dev.tfvars
   terraform apply -var-file=environments/dev.tfvars
   ```

3. **Deploy Notebooks**:
   ```bash
   ./scripts/deploy_notebooks.sh dev
   ```

4. **Setup Unity Catalog**:
   ```bash
   ./scripts/setup_unity_catalog.sh
   ```

5. **Deploy Airflow DAGs**:
   ```bash
   # Copy DAGs to Airflow DAGs folder
   cp -r airflow/dags/* /path/to/airflow/dags/
   ```

## Environments

- **Dev**: Development environment for testing
- **QA**: Quality assurance environment for validation
- **Prod**: Production environment for live data

## Documentation

- [Architecture Documentation](architecture.md)
- [Operational Runbook](runbook.md)
- [Unity Catalog Setup](governance/unity_catalog_grants.sql)

## License

MIT


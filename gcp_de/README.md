# Retail Data Lake + Data Warehouse on Google Cloud Platform

A modern, production-ready data engineering solution built on GCP-native services, supporting both streaming and batch data ingestion with medallion architecture (bronze/silver/gold zones).

## Architecture Overview

### High-Level Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    Source Systems                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Transactional│  │  File Dumps  │  │   External   │         │
│  │    Database  │  │   (CSV/JSON) │  │   Systems    │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          │ CDC/Streaming    │ Batch            │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Ingestion Layer                               │
│  ┌──────────────────┐              ┌──────────────────┐        │
│  │  Cloud Pub/Sub   │              │  Cloud Storage   │        │
│  │  (Streaming)     │              │  (Batch Landing) │        │
│  └────────┬─────────┘              └────────┬─────────┘        │
│           │                                 │                   │
│           └──────────────┬──────────────────┘                   │
│                          ▼                                      │
│              ┌──────────────────────┐                           │
│              │  Dataflow (Beam)     │                           │
│              │  - Streaming Jobs    │                           │
│              │  - Batch Jobs        │                           │
│              └──────────┬───────────┘                           │
└─────────────────────────┼───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Lake (GCS)                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Raw Zone    │  │ Staging Zone │  │ Curated Zone │         │
│  │  (Bronze)    │  │  (Silver)    │  │   (Gold)     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Warehouse (BigQuery)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Staging    │  │   Curated    │  │   Analytics  │         │
│  │   Datasets   │  │   Datasets   │  │   Datasets   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Orchestration (Cloud Composer)                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Airflow DAGs                                             │  │
│  │  - Batch ETL DAGs                                         │  │
│  │  - Streaming Pipeline DAGs                                │  │
│  │  - Data Quality DAGs                                      │  │
│  │  - SCD Type 1/2 DAGs                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Governance & Metadata                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Data Catalog │  │  Cloud Logging│  │  Monitoring  │         │
│  │  / Dataplex  │  │               │  │              │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
.
├── README.md
├── architecture.md
├── terraform/
│   ├── environments/
│   │   ├── dev/
│   │   ├── qa/
│   │   └── prod/
│   ├── modules/
│   │   ├── gcs/
│   │   ├── pubsub/
│   │   ├── bigquery/
│   │   ├── composer/
│   │   ├── dataflow/
│   │   └── iam/
│   └── main.tf
├── airflow/
│   ├── dags/
│   │   ├── batch_etl_dag.py
│   │   ├── streaming_pipeline_dag.py
│   │   ├── scd_dimension_dag.py
│   │   └── data_quality_dag.py
│   └── plugins/
├── dataflow/
│   ├── streaming/
│   │   └── pubsub_to_gcs_bigquery.py
│   ├── batch/
│   │   └── gcs_transform_pipeline.py
│   └── requirements.txt
├── bigquery/
│   ├── schemas/
│   ├── transformations/
│   ├── scd/
│   └── fact_loads/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── data_quality/
├── ci-cd/
│   └── .github/
│       └── workflows/
└── runbooks/
    ├── operations.md
    ├── failure_recovery.md
    └── data_onboarding.md
```

## Environments

- **Development**: Initial development and testing
- **QA**: Quality assurance and integration testing
- **Production**: Live production workloads

Each environment has:
- Separate GCP project (or logical separation)
- Isolated Cloud Composer environment
- Separate Terraform state
- Environment-specific configurations

## Getting Started

### Prerequisites

- Google Cloud SDK (gcloud) installed and configured
- Terraform >= 1.0
- Python 3.9+
- Access to GCP project with appropriate permissions

### Setup

1. **Configure GCP Authentication**
   ```bash
   gcloud auth application-default login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Initialize Terraform**
   ```bash
   cd terraform/environments/dev
   terraform init
   ```

3. **Deploy Infrastructure**
   ```bash
   terraform plan
   terraform apply
   ```

4. **Deploy Dataflow Pipelines**
   ```bash
   cd ../../dataflow
   pip install -r requirements.txt
   # Deploy via CI/CD or manually
   ```

5. **Deploy Airflow DAGs**
   - DAGs are automatically synced to Cloud Composer GCS bucket
   - Or manually upload via `gcloud composer` commands

## Key Features

- **Medallion Architecture**: Raw → Staging → Curated data zones
- **Streaming & Batch**: Unified ingestion via Pub/Sub and GCS
- **SCD Support**: Type 1 and Type 2 slowly changing dimensions
- **Multi-Environment**: Dev, QA, Production with proper isolation
- **Infrastructure as Code**: Complete Terraform automation
- **CI/CD**: Automated deployment via GitHub Actions
- **Data Quality**: Automated validation and monitoring
- **Governance**: Data Catalog integration for metadata management

## Documentation

- [Architecture Details](architecture.md)
- [Runbooks](runbooks/operations.md)
- [Data Onboarding Guide](runbooks/data_onboarding.md)
- [Failure Recovery](runbooks/failure_recovery.md)

## License

Proprietary - Internal Use Only


# GCP Bigtable Data Engineering Pipeline

A production-ready data engineering project demonstrating a complete data pipeline using Google Cloud Bigtable with infrastructure as code, CI/CD automation, and comprehensive data quality checks.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Source Data                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   CSV Files  │  │  JSON Events │  │  Pub/Sub     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Pipeline (Python)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Ingestion   │→ │ Transform    │→ │ Data Quality │          │
│  │   (Batch)    │  │  & Enrich    │  │    Checks    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Google Cloud Bigtable                               │
│  ┌────────────────────────┐  ┌────────────────────────┐        │
│  │   Fact Table           │  │   Aggregate Table      │        │
│  │  (raw events)          │  │  (daily/weekly rollups)│        │
│  └────────────────────────┘  └────────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Query Layer                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Python API  │  │  Jupyter     │  │  REST API    │          │
│  │   Client     │  │  Notebooks   │  │  (optional)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘

Infrastructure: Terraform + Ansible
CI/CD: GitHub Actions
Monitoring: Cloud Logging + Alerts
```

## Project Structure

```
.
├── terraform/                 # Infrastructure as Code
│   ├── modules/              # Reusable Terraform modules
│   │   ├── bigtable/        # Bigtable instance and tables
│   │   ├── networking/      # VPC, subnets, firewall rules
│   │   └── service-accounts/ # IAM and service accounts
│   ├── environments/         # Environment-specific configs
│   │   ├── dev/
│   │   ├── staging/
│   │   └── production/
│   └── main.tf              # Root module
│
├── ansible/                  # Configuration Management
│   ├── playbooks/
│   │   ├── setup.yml        # Main setup playbook
│   │   └── deploy-pipeline.yml
│   ├── roles/
│   │   ├── python-runtime/  # Python installation
│   │   ├── bigtable-client/ # Bigtable client setup
│   │   └── pipeline-service/ # Pipeline service deployment
│   └── inventory/
│       ├── dev.yml
│       ├── staging.yml
│       └── production.yml
│
├── .github/
│   └── workflows/
│       ├── terraform-validate.yml
│       ├── terraform-apply.yml
│       └── pipeline-tests.yml
│
├── pipelines/                # Data Pipeline Code
│   ├── ingestion/           # Data ingestion scripts
│   │   ├── batch_ingestion.py
│   │   └── stream_ingestion.py (optional)
│   ├── transformation/      # Data transformation logic
│   │   └── transform.py
│   ├── quality/             # Data quality checks
│   │   └── quality_checks.py
│   ├── aggregation/         # Aggregation logic
│   │   └── aggregator.py
│   └── utils/               # Utility functions
│       ├── bigtable_client.py
│       └── retry_handler.py
│
├── queries/                  # Sample Queries
│   ├── sample_queries.py
│   └── example_notebook.ipynb
│
├── tests/                    # Unit and Integration Tests
│   ├── unit/
│   └── integration/
│
├── data/                     # Sample Data
│   └── sample_events.csv
│
└── docs/                     # Additional Documentation
    └── architecture.md
```

## Prerequisites

### GCP Setup
1. Google Cloud Project with billing enabled
2. GCP Account with necessary permissions:
   - Bigtable Admin
   - Compute Admin
   - Service Account Admin
   - IAM Admin
3. Enable required APIs:
   ```bash
   gcloud services enable bigtable.googleapis.com
   gcloud services enable compute.googleapis.com
   gcloud services enable iam.googleapis.com
   ```

### Local Tools
- Terraform >= 1.0
- Ansible >= 2.9
- Python >= 3.9
- Google Cloud SDK (gcloud CLI)
- Docker (optional, for local testing)

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd cursor_GCP_BigTable_NoSql_DE
```

### 2. Configure GitHub Secrets

Set up the following secrets in your GitHub repository:
- `GCP_PROJECT_ID`: Your GCP project ID
- `GCP_SA_KEY`: Service account key JSON (base64 encoded)
- `GCP_SA_EMAIL`: Service account email
- `TF_STATE_BUCKET`: GCS bucket for Terraform state (optional)
- `SLACK_WEBHOOK_URL`: For alerts (optional)

### 3. Terraform Deployment

#### Development Environment
```bash
cd terraform/environments/dev
terraform init
terraform plan
terraform apply
```

#### Production Environment
```bash
cd terraform/environments/production
terraform init
terraform plan
terraform apply
```

### 4. Ansible Configuration

```bash
cd ansible
ansible-playbook -i inventory/dev.yml playbooks/setup.yml
```

### 5. Run Data Pipeline

```bash
# Install Python dependencies
pip install -r pipelines/requirements.txt

# Set environment variables
export GCP_PROJECT_ID="your-project-id"
export BIGTABLE_INSTANCE="your-instance-id"
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"

# Run batch ingestion
python pipelines/ingestion/batch_ingestion.py --source data/sample_events.csv
```

## Detailed Documentation

### Terraform Deployment

See [terraform/README.md](terraform/README.md) for detailed Terraform deployment instructions.

### Ansible Configuration

See [ansible/README.md](ansible/README.md) for Ansible playbook usage.

### CI/CD Pipeline

See [.github/workflows/README.md](.github/workflows/README.md) for GitHub Actions workflow details.

### Data Pipeline

See [pipelines/README.md](pipelines/README.md) for data pipeline documentation and usage.

## Sample Queries

### Query Events by User
```python
from pipelines.utils.bigtable_client import BigTableClient

client = BigTableClient()
events = client.get_user_events(user_id="user123", limit=100)
```

### Get Daily Aggregates
```python
aggregates = client.get_daily_aggregates(date="2024-01-15")
```

See [queries/sample_queries.py](queries/sample_queries.py) for more examples.

## Data Quality Checks

The pipeline includes automatic data quality checks:
- Schema validation (required fields, types)
- Duplicate detection
- Missing value detection
- Data freshness checks

Quality failures trigger alerts via Cloud Logging and optional Slack notifications.

## Monitoring and Alerting

- Cloud Logging: All pipeline operations are logged
- Cloud Monitoring: Metrics for ingestion rate, quality failures, latency
- Alerts: Configured for data quality failures and pipeline errors

## Environment Variables

```bash
# GCP Configuration
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1
BIGTABLE_INSTANCE=bigtable-instance-name

# Authentication
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Pipeline Configuration
BATCH_SIZE=1000
QUALITY_CHECK_ENABLED=true
ALERT_WEBHOOK_URL=https://hooks.slack.com/...
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests: `pytest tests/`
4. Submit a pull request

## License

MIT License

## Support

For issues and questions, please open an issue in the repository.

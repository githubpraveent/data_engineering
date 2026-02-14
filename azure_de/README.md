# Azure Retail Data Lake & Data Warehouse

A production-grade retail data lake and data warehouse solution on Azure with streaming and batch ingestion, CDC, data transformation, and SCD dimension handling.

## Architecture Overview

This solution implements a modern data architecture on Azure with the following components:

### Ingestion Layer
- **Azure Event Hubs**: Real-time event streaming from POS systems and operational databases
- **Azure Data Factory**: Batch ingestion orchestration
- **CDC**: Change Data Capture for incremental data loading

### Storage Layer
- **Azure Data Lake Storage Gen2**: Medallion architecture (Bronze/Raw, Silver/Staging, Gold/Curated)
- **Lifecycle Management**: Automated tiering and retention policies

### Transformation Layer
- **Azure Databricks**: Spark-based ETL with Delta Lake
- **Delta Lake**: ACID transactions, schema evolution, time-travel

### Orchestration
- **Apache Airflow**: Deployed on Azure Kubernetes Service (AKS)
- **DAGs**: Coordinate ingestion, transformation, and data warehouse loads

### Data Warehouse
- **Azure Synapse Analytics**: SQL Pool for analytical workloads
- **SCD Implementation**: Type 1 and Type 2 slowly changing dimensions
- **Fact Tables**: Incremental and append loads

### Governance
- **Azure Purview**: Data catalog, lineage, and governance
- **RBAC**: Azure AD-based access control

### Infrastructure & DevOps
- **Terraform**: Infrastructure as Code
- **GitHub Actions**: CI/CD pipelines
- **Multi-Environment**: Dev, QA, Production

## Project Structure

```
.
├── README.md
├── docs/
│   ├── architecture.md
│   ├── runbook.md
│   ├── onboarding-guide.md
│   └── governance-plan.md
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── modules/
│   │   ├── adls/
│   │   ├── event-hubs/
│   │   ├── databricks/
│   │   ├── synapse/
│   │   ├── airflow-aks/
│   │   ├── purview/
│   │   └── key-vault/
│   └── environments/
│       ├── dev/
│       ├── qa/
│       └── prod/
├── airflow/
│   ├── dags/
│   │   ├── ingestion/
│   │   ├── transformation/
│   │   └── warehouse/
│   ├── plugins/
│   └── requirements.txt
├── databricks/
│   ├── notebooks/
│   │   ├── ingestion/
│   │   ├── transformation/
│   │   └── quality/
│   └── jobs/
├── synapse/
│   ├── schemas/
│   ├── dimensions/
│   ├── facts/
│   └── stored-procedures/
├── adf/
│   └── pipelines/
├── ci-cd/
│   └── .github/
│       └── workflows/
└── tests/
    ├── unit/
    ├── integration/
    └── data-quality/
```

## Getting Started

### Prerequisites
- Azure subscription with appropriate permissions
- Terraform >= 1.0
- Azure CLI installed and configured
- kubectl (for AKS/Airflow)
- Python 3.8+ (for Airflow and Databricks)

### Quick Start

1. **Configure Terraform variables**:
   ```bash
   cd terraform/environments/dev
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   ```

2. **Deploy Infrastructure**:
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

3. **Deploy Airflow DAGs**:
   ```bash
   # Configure Airflow connection to Azure
   # Deploy DAGs via CI/CD or manually
   ```

4. **Deploy Databricks Notebooks**:
   ```bash
   # Use Databricks CLI or CI/CD pipeline
   ```

5. **Deploy Synapse Scripts**:
   ```bash
   # Run SQL scripts via Azure CLI or Synapse Studio
   ```

## Environment Strategy

- **Dev**: Development and testing environment
- **QA**: Quality assurance and integration testing
- **Prod**: Production environment with enhanced monitoring and security

Each environment is provisioned via Terraform with environment-specific configurations.

## Documentation

- [Architecture Details](docs/architecture.md)
- [Operational Runbook](docs/runbook.md)
- [Onboarding Guide](docs/onboarding-guide.md)
- [Governance Plan](docs/governance-plan.md)

## Contributing

Follow the branching strategy:
- `dev` branch for development
- `qa` branch for QA environment
- `main` branch for production

All changes go through CI/CD pipelines with automated testing.


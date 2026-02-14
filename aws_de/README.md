# Retail Data Lake & Data Warehouse on AWS

A comprehensive data engineering solution for ingesting, processing, and storing retail data from Azure SQL Server to AWS, supporting streaming, batch, and CDC workloads.

## Architecture Overview

### High-Level Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    Azure SQL Server (Source)                     │
│                    (CDC Enabled)                                │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ Kafka Producers (CDC Events)
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│              Amazon MSK (Kafka Cluster)                         │
│  Topics: customer_changes, order_changes, product_changes, etc. │
└──────────────┬──────────────────────────────┬───────────────────┘
               │                              │
               │                              │
    ┌──────────▼──────────┐      ┌───────────▼────────────┐
    │  Glue Streaming Job  │      │  Redshift Streaming   │
    │  (MSK → S3)          │      │  (MSK → Redshift MV)  │
    └──────────┬───────────┘      └───────────┬───────────┘
               │                              │
               │                              │
    ┌──────────▼──────────┐      ┌───────────▼────────────┐
    │   S3 Data Lake       │      │   Amazon Redshift     │
    │   (Medallion Arch)   │      │   (Data Warehouse)    │
    │   - Landing (Raw)    │      │   - Staging Schema    │
    │   - Staging          │      │   - Star Schema       │
    │   - Curated          │      │   - SCD Dimensions    │
    └──────────┬───────────┘      └───────────────────────┘
               │
               │
    ┌──────────▼──────────┐
    │   Glue Batch Jobs    │
    │   (S3 Transform)    │
    └──────────┬───────────┘
               │
               │
    ┌──────────▼──────────┐
    │   Glue Data Catalog  │
    │   (Metadata)         │
    └──────────────────────┘
```

### Data Flow

1. **Ingestion**: Azure SQL Server CDC → Kafka Producers → Amazon MSK
2. **Streaming**: MSK → Glue Streaming Jobs → S3 (Landing Zone)
3. **Streaming to DW**: MSK → Redshift Streaming Ingestion (Materialized Views)
4. **Batch Processing**: S3 Landing → Glue Batch Jobs → S3 Staging/Curated
5. **Warehouse Loading**: S3 Curated → Redshift Staging → SCD/Fact Processing → Star Schema

### S3 Data Lake Structure (Medallion Architecture)

```
s3://retail-datalake-{env}/
├── landing/              # Raw CDC events from Kafka
│   ├── customer/
│   ├── order/
│   └── product/
├── staging/              # Cleaned, validated data
│   ├── customer/
│   ├── order/
│   └── product/
└── curated/              # Business-ready, transformed data
    ├── dimensions/
    └── facts/
```

## Project Structure

```
.
├── terraform/              # Infrastructure as Code
│   ├── environments/      # Environment-specific configs
│   ├── modules/           # Reusable Terraform modules
│   └── main.tf           # Root module
├── ansible/               # Configuration management
│   ├── playbooks/
│   └── roles/
├── glue/                  # AWS Glue ETL jobs
│   ├── streaming/
│   ├── batch/
│   └── tests/
├── redshift/              # Redshift SQL scripts
│   ├── schemas/
│   ├── scd/
│   └── facts/
├── .github/               # GitHub Actions workflows
│   └── workflows/
├── tests/                 # Test scripts and harnesses
│   ├── kafka/
│   ├── glue/
│   └── redshift/
└── docs/                  # Documentation
    ├── architecture.md
    └── runbooks/
```

## Prerequisites

- AWS Account with appropriate permissions
- Terraform >= 1.0
- Ansible >= 2.9
- Python 3.8+ (for Glue jobs and tests)
- AWS CLI configured
- GitHub repository for CI/CD

## Quick Start

### 1. Configure Environments

Edit `terraform/environments/{env}/terraform.tfvars` for each environment (dev, qa, prod).

### 2. Deploy Infrastructure

```bash
# Initialize Terraform
cd terraform
terraform init

# Select workspace
terraform workspace select dev

# Plan
terraform plan

# Apply
terraform apply
```

### 3. Deploy Configuration

```bash
cd ansible
ansible-playbook -i inventory/dev playbooks/kafka-setup.yml
```

### 4. Deploy Glue Jobs

Glue jobs are deployed via GitHub Actions CI/CD pipeline. See `.github/workflows/deploy-glue.yml`.

### 5. Deploy Redshift Schemas

```bash
cd redshift
# Run schema migrations via CI/CD or manually
psql -h <redshift-endpoint> -U <user> -d <database> -f schemas/staging.sql
```

## Environment Management

The project supports three environments:
- **dev**: Development environment
- **qa**: QA/Testing environment  
- **prod**: Production environment

Each environment is managed via Terraform workspaces and GitHub branch strategy:
- `main` branch → Production
- `qa` branch → QA environment
- `dev` branch → Development environment

## CI/CD Pipeline

GitHub Actions workflows handle:
- Terraform validation and deployment
- Glue job deployment
- Redshift schema migrations
- Automated testing
- Rollback capabilities

See `.github/workflows/` for workflow definitions.

## Testing

Run tests for each component:

```bash
# Kafka tests
python tests/kafka/test_topic_validation.py

# Glue ETL tests
python tests/glue/test_etl_transformations.py

# Redshift validation
python tests/redshift/test_data_quality.py
```

## Monitoring

- **CloudWatch**: Glue job metrics, MSK metrics, Redshift performance
- **Glue Data Catalog**: Data lineage and schema evolution
- **Kafka Schema Registry**: Schema validation and evolution

## Adding New Source Tables

1. Create Kafka topic in `terraform/modules/msk/topics.tf`
2. Add Glue streaming job in `glue/streaming/`
3. Create Redshift staging table in `redshift/schemas/staging.sql`
4. Add SCD/fact processing in `redshift/scd/` or `redshift/facts/`
5. Update tests in `tests/`

See `docs/runbooks/onboarding-new-tables.md` for detailed steps.

## Documentation

- [Architecture Details](docs/architecture.md)
- [Runbooks](docs/runbooks/)
- [Terraform Modules](terraform/modules/README.md)
- [Glue Jobs](glue/README.md)
- [Redshift Schema](redshift/README.md)

## License

MIT


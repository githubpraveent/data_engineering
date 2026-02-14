# CI/CD Workflows

This directory contains GitHub Actions workflows for automated deployment and testing.

## Workflows

### 1. Terraform Infrastructure Deployment (`terraform.yml`)
- **Triggers**: Push to main/dev/qa branches when `terraform/**` changes
- **Actions**:
  - Validates Terraform code
  - Runs `terraform plan`
  - Applies changes to appropriate environment
- **Environments**: dev, qa, prod

### 2. Dataflow Pipeline Deployment (`dataflow.yml`)
- **Triggers**: Push to main/dev/qa branches when `dataflow/**` changes
- **Actions**:
  - Builds Dataflow pipeline package
  - Deploys streaming and batch pipeline templates to GCS
  - Runs unit tests
- **Environments**: dev, qa, prod

### 3. Airflow DAG Deployment (`airflow.yml`)
- **Triggers**: Push to main/dev/qa branches when `airflow/dags/**` changes
- **Actions**:
  - Validates DAG syntax
  - Copies DAGs to Cloud Composer GCS bucket
  - Verifies deployment
- **Environments**: dev, qa, prod

### 4. BigQuery Schema Deployment (`bigquery.yml`)
- **Triggers**: Push to main/dev/qa branches when `bigquery/**` changes
- **Actions**:
  - Deploys staging, curated, and analytics table schemas
  - Loads date dimension table
- **Environments**: dev, qa, prod

### 5. Tests (`tests.yml`)
- **Triggers**: Push and pull requests
- **Actions**:
  - Unit tests for Dataflow pipelines
  - Integration tests
  - Data quality tests
  - Code linting
- **Environments**: dev (for integration tests)

## Required Secrets

Configure the following secrets in GitHub repository settings:

- `GCP_SA_KEY`: Service account JSON key for GCP authentication
- `GCP_PROJECT_DEV`: Development GCP project ID
- `GCP_PROJECT_QA`: QA GCP project ID
- `GCP_PROJECT_PROD`: Production GCP project ID

## Environment Protection

Production environment requires:
- Manual approval for deployments
- Branch protection rules
- Required status checks

## Manual Deployment

You can trigger workflows manually using `workflow_dispatch`:

```bash
gh workflow run terraform.yml -f environment=dev
gh workflow run dataflow.yml -f environment=qa
```

## Rollback Strategy

1. **Terraform**: Revert to previous commit and re-run workflow
2. **Dataflow**: Deploy previous template version
3. **Airflow**: Revert DAG files and re-deploy
4. **BigQuery**: Use point-in-time recovery or restore from backup


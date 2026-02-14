# Quick Start Guide

This guide helps you get started with the Azure Retail Data Lake and Data Warehouse solution.

## Prerequisites

Before you begin, ensure you have:
- Azure subscription with appropriate permissions
- Terraform >= 1.0 installed
- Azure CLI installed and configured
- Python 3.8+ installed
- kubectl installed (for AKS/Airflow)
- Git installed

## Step 1: Clone Repository

```bash
git clone <repository-url>
cd cursor_Azure_DE
```

## Step 2: Configure Azure

```bash
# Login to Azure
az login

# Set subscription
az account set --subscription <subscription-id>

# Create service principal (if needed)
az ad sp create-for-rbac --name "retail-datalake-sp" --role contributor
```

## Step 3: Configure Terraform

```bash
cd terraform/environments/dev

# Copy example variables
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your values
# - Set environment, project_name, location
# - Configure resource sizes
# - Set tags
```

## Step 4: Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Review plan
terraform plan

# Apply (creates all Azure resources)
terraform apply
```

This will create:
- Resource Group
- ADLS Gen2 Storage Account
- Event Hubs Namespace
- Databricks Workspace
- Synapse Analytics Workspace
- AKS Cluster (for Airflow)
- Purview Account
- Key Vault

## Step 5: Configure Secrets

```bash
# Store secrets in Key Vault
az keyvault secret set \
  --vault-name <key-vault-name> \
  --name "event-hubs-connection-string" \
  --value "<connection-string>"
```

## Step 6: Deploy Databricks Notebooks

```bash
# Install Databricks CLI
pip install databricks-cli

# Configure CLI
databricks configure --token

# Deploy notebooks
databricks workspace import_dir databricks/notebooks/ingestion /Shared/ingestion -o
databricks workspace import_dir databricks/notebooks/transformation /Shared/transformation -o
databricks workspace import_dir databricks/notebooks/quality /Shared/quality -o
```

## Step 7: Deploy Synapse Schemas

```bash
# Connect to Synapse
az synapse sql-script create \
  --workspace-name <synapse-workspace> \
  --resource-group <rg> \
  --file synapse/schemas/staging_schema.sql \
  --name staging_schema

# Deploy all schemas and stored procedures
# (See synapse-deployment.yml for full script)
```

## Step 8: Deploy Airflow

```bash
# Get AKS credentials
az aks get-credentials --resource-group <rg> --name <aks-cluster>

# Deploy Airflow (using Helm or kubectl)
# See Airflow deployment documentation

# Copy DAGs
kubectl cp airflow/dags/ <namespace>/<airflow-pod>:/opt/airflow/dags/
```

## Step 9: Configure Airflow Connections

In Airflow UI:
1. Go to Admin → Connections
2. Add connections:
   - `databricks_default`: Databricks workspace
   - `azure_data_factory_default`: Data Factory
   - `synapse_sql_pool`: Synapse SQL Pool
   - `azure_key_vault`: Key Vault

## Step 10: Test End-to-End

1. **Send Test Events to Event Hubs**
   ```bash
   # Use Event Hubs Explorer or send test events
   ```

2. **Trigger Ingestion DAG**
   - Airflow UI → DAGs → `ingest_pos_events_stream` → Trigger

3. **Verify Data Flow**
   - Check ADLS Bronze container
   - Check Databricks notebooks execution
   - Check Synapse warehouse

## Step 11: Set Up CI/CD

1. **Configure GitHub Secrets**
   - Go to GitHub → Settings → Secrets
   - Add Azure credentials
   - Add service connection details

2. **Push to Repository**
   ```bash
   git add .
   git commit -m "Initial setup"
   git push origin dev
   ```

3. **CI/CD Will**
   - Run tests
   - Deploy infrastructure (if Terraform changes)
   - Deploy code (Databricks, Airflow, Synapse)

## Next Steps

- Read [Architecture Documentation](docs/architecture.md)
- Review [Operational Runbook](docs/runbook.md)
- Check [Onboarding Guide](docs/onboarding-guide.md) for adding new sources
- Review [Governance Plan](docs/governance-plan.md)

## Troubleshooting

### Terraform Errors
- Check Azure permissions
- Verify variable values
- Review Terraform logs

### Databricks Issues
- Verify workspace URL
- Check service principal permissions
- Review notebook logs

### Airflow Issues
- Check pod status: `kubectl get pods -n <namespace>`
- View logs: `kubectl logs <airflow-pod>`
- Check connections in Airflow UI

### Synapse Issues
- Verify SQL Pool is running
- Check firewall rules
- Review query history

## Support

For issues or questions:
- **Data Engineering Team**: data-engineering@company.com
- **Documentation**: See docs/ directory
- **GitHub Issues**: Create issue in repository


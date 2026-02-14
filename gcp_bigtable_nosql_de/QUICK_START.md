# Quick Start Guide

Get up and running with the GCP Bigtable Data Engineering Pipeline in minutes.

## Prerequisites Checklist

- [ ] GCP Project created with billing enabled
- [ ] Required APIs enabled (Bigtable, Compute, IAM, Logging, Monitoring)
- [ ] Service accounts created with appropriate permissions
- [ ] GitHub repository with secrets configured
- [ ] Terraform >= 1.0 installed
- [ ] Ansible >= 2.9 installed
- [ ] Python 3.9+ installed
- [ ] Google Cloud SDK installed and authenticated

## Quick Setup (5 Steps)

### 1. Clone and Configure

```bash
git clone <your-repo-url>
cd cursor_GCP_BigTable_NoSql_DE
```

### 2. Deploy Infrastructure

```bash
cd terraform/environments/dev
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your GCP project ID
terraform init
terraform plan
terraform apply
```

### 3. Configure Servers (if deploying to VMs)

```bash
cd ../../..  # Back to project root
# Edit ansible/inventory/dev.yml with your server IPs
ansible-playbook -i ansible/inventory/dev.yml ansible/playbooks/setup.yml \
  --extra-vars "gcp_project_id=your-project-id"
```

### 4. Install Python Dependencies

```bash
pip install -r pipelines/requirements.txt
```

### 5. Run Pipeline

```bash
# Set environment variables
export GCP_PROJECT_ID="your-project-id"
export BIGTABLE_INSTANCE="dev-bigtable-instance"  # From terraform output
export GOOGLE_APPLICATION_CREDENTIALS="./pipeline-sa-key.json"

# Ingest sample data
python pipelines/ingestion/batch_ingestion.py \
  --source data/sample_events.csv \
  --project-id $GCP_PROJECT_ID \
  --instance-id $BIGTABLE_INSTANCE

# Run aggregation
python pipelines/aggregation/aggregator.py \
  --project-id $GCP_PROJECT_ID \
  --instance-id $BIGTABLE_INSTANCE

# Test queries
python queries/sample_queries.py
```

## Common Commands

### Terraform

```bash
# Initialize
terraform init

# Plan changes
terraform plan

# Apply changes
terraform apply

# Destroy (careful!)
terraform destroy
```

### Pipeline

```bash
# Batch ingestion
python pipelines/ingestion/batch_ingestion.py --source data/file.csv

# Aggregation job
python pipelines/aggregation/aggregator.py --date 2024-01-15

# Run tests
pytest tests/unit/ -v
```

### GitHub Actions

- **Terraform Validate**: Runs automatically on PR
- **Terraform Apply**: Manual trigger from Actions tab
- **Pipeline Tests**: Runs automatically on push/PR
- **Promote to Production**: Manual workflow dispatch

## Verify Deployment

```bash
# Check Bigtable instance
gcloud bigtable instances list

# Check tables
gcloud bigtable instances tables list dev-bigtable-instance

# View logs
gcloud logging read "resource.type=bigtable_instance" --limit 20

# Run queries
python queries/sample_queries.py
```

## Next Steps

1. Review [SETUP.md](SETUP.md) for detailed setup instructions
2. Read [docs/architecture.md](docs/architecture.md) for architecture details
3. Check [pipelines/README.md](pipelines/README.md) for pipeline usage
4. See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines

## Troubleshooting

**Issue**: `Permission denied` errors
- **Solution**: Check service account permissions and IAM roles

**Issue**: `Table not found` errors
- **Solution**: Verify table names match Terraform outputs

**Issue**: Ansible connection errors
- **Solution**: Check SSH connectivity and inventory file

**Issue**: GitHub Actions failing
- **Solution**: Verify secrets are configured correctly

## Getting Help

- Review the main [README.md](README.md)
- Check [SETUP.md](SETUP.md) for detailed instructions
- Open an issue in the repository
- Check GCP logs for detailed error messages

# Setup Guide

Complete setup instructions for the GCP Bigtable Data Engineering Pipeline.

## Prerequisites

### 1. Google Cloud Platform Setup

1. Create a GCP Project (if not already exists):
   ```bash
   gcloud projects create your-project-id
   gcloud config set project your-project-id
   ```

2. Enable billing for your project

3. Enable required APIs:
   ```bash
   gcloud services enable bigtable.googleapis.com
   gcloud services enable compute.googleapis.com
   gcloud services enable iam.googleapis.com
   gcloud services enable logging.googleapis.com
   gcloud services enable monitoring.googleapis.com
   ```

4. Create a service account for the pipeline:
   ```bash
   gcloud iam service-accounts create pipeline-sa \
     --display-name="Data Pipeline Service Account"
   
   gcloud projects add-iam-policy-binding your-project-id \
     --member="serviceAccount:pipeline-sa@your-project-id.iam.gserviceaccount.com" \
     --role="roles/bigtable.user"
   
   gcloud iam service-accounts keys create pipeline-sa-key.json \
     --iam-account=pipeline-sa@your-project-id.iam.gserviceaccount.com
   ```

5. Create a service account for GitHub Actions:
   ```bash
   gcloud iam service-accounts create github-actions-sa \
     --display-name="GitHub Actions Service Account"
   
   gcloud projects add-iam-policy-binding your-project-id \
     --member="serviceAccount:github-actions-sa@your-project-id.iam.gserviceaccount.com" \
     --role="roles/bigtable.admin"
   
   gcloud projects add-iam-policy-binding your-project-id \
     --member="serviceAccount:github-actions-sa@your-project-id.iam.gserviceaccount.com" \
     --role="roles/compute.admin"
   
   gcloud iam service-accounts keys create github-actions-key.json \
     --iam-account=github-actions-sa@your-project-id.iam.gserviceaccount.com
   ```

### 2. Local Development Setup

1. Install Terraform:
   ```bash
   # macOS
   brew install terraform
   
   # Linux
   wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
   unzip terraform_1.6.0_linux_amd64.zip
   sudo mv terraform /usr/local/bin/
   ```

2. Install Ansible:
   ```bash
   pip install ansible
   ```

3. Install Python 3.9+:
   ```bash
   python3 --version  # Should be 3.9 or higher
   ```

4. Install Google Cloud SDK:
   ```bash
   # macOS
   brew install google-cloud-sdk
   
   # Or follow: https://cloud.google.com/sdk/docs/install
   ```

5. Authenticate with GCP:
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

### 3. GitHub Setup

1. Fork or create a new repository

2. Configure GitHub Secrets (Settings → Secrets and variables → Actions):
   - `GCP_PROJECT_ID`: Your GCP project ID
   - `GCP_SA_KEY`: Contents of `github-actions-key.json` (base64 encoded)
   - `GCP_SA_EMAIL`: `github-actions-sa@your-project-id.iam.gserviceaccount.com`
   - `BIGTABLE_INSTANCE`: Will be set after Terraform deployment
   - `SLACK_WEBHOOK_URL`: (Optional) Slack webhook URL for alerts

3. Configure Environment Protection:
   - Go to Settings → Environments
   - Create `dev`, `staging`, `production` environments
   - For `production`, add required reviewers

## Deployment Steps

### Step 1: Deploy Infrastructure (Terraform)

1. Navigate to dev environment:
   ```bash
   cd terraform/environments/dev
   ```

2. Create `terraform.tfvars`:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   ```

3. Initialize Terraform:
   ```bash
   terraform init
   ```

4. Plan changes:
   ```bash
   terraform plan
   ```

5. Apply changes:
   ```bash
   terraform apply
   ```

6. Note the outputs (Bigtable instance name, etc.)

### Step 2: Configure Servers (Ansible)

1. Update inventory file with actual server IPs:
   ```bash
   # Edit ansible/inventory/dev.yml
   ```

2. Run Ansible playbook:
   ```bash
   ansible-playbook -i ansible/inventory/dev.yml ansible/playbooks/setup.yml \
     --extra-vars "gcp_project_id=your-project-id" \
     --extra-vars "bigtable_instance_id=dev-bigtable-instance" \
     --extra-vars "service_account_key_path=./pipeline-sa-key.json"
   ```

### Step 3: Run Data Pipeline

1. Set environment variables:
   ```bash
   export GCP_PROJECT_ID="your-project-id"
   export BIGTABLE_INSTANCE="dev-bigtable-instance"
   export GOOGLE_APPLICATION_CREDENTIALS="./pipeline-sa-key.json"
   ```

2. Install Python dependencies:
   ```bash
   pip install -r pipelines/requirements.txt
   ```

3. Run batch ingestion:
   ```bash
   python pipelines/ingestion/batch_ingestion.py \
     --source data/sample_events.csv \
     --format csv \
     --project-id your-project-id \
     --instance-id dev-bigtable-instance
   ```

4. Run aggregation job:
   ```bash
   python pipelines/aggregation/aggregator.py \
     --project-id your-project-id \
     --instance-id dev-bigtable-instance \
     --date 2024-01-15
   ```

### Step 4: Test Queries

1. Run sample queries:
   ```bash
   python queries/sample_queries.py
   ```

## Verification

1. Check Bigtable instance:
   ```bash
   gcloud bigtable instances list
   ```

2. Check tables:
   ```bash
   gcloud bigtable instances tables list dev-bigtable-instance
   ```

3. View logs:
   ```bash
   gcloud logging read "resource.type=bigtable_instance" --limit 50
   ```

## Troubleshooting

### Terraform Issues

- **Error: Project not found**: Verify project ID
- **Error: Permission denied**: Check service account permissions
- **Error: Resource already exists**: Import existing resources or destroy first

### Ansible Issues

- **Error: Host unreachable**: Check SSH connectivity and firewall rules
- **Error: Permission denied**: Use `--become` flag or configure sudo

### Pipeline Issues

- **Error: Authentication failed**: Check service account key path and permissions
- **Error: Table not found**: Verify table names and instance ID
- **Error: Quality check failures**: Review data format and required fields

## Next Steps

- Configure monitoring and alerting
- Set up scheduled aggregation jobs (cron/systemd)
- Implement streaming ingestion (if needed)
- Set up data retention policies
- Configure backups

## Support

For issues, please open an issue in the repository.

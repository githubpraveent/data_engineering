# Terraform Infrastructure

This directory contains Terraform configurations for provisioning GCP resources for the Bigtable data pipeline.

## Structure

```
terraform/
├── modules/              # Reusable modules
│   ├── bigtable/        # Bigtable instance and tables
│   ├── networking/      # VPC and networking
│   └── service-accounts/ # IAM and service accounts
└── environments/        # Environment-specific configs
    ├── dev/
    ├── staging/
    └── production/
```

## Prerequisites

1. Install Terraform >= 1.0
2. Authenticate with GCP:
   ```bash
   gcloud auth application-default login
   ```
3. Set your project:
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```

## Usage

### Development Environment

1. Navigate to the dev directory:
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

### Staging/Production

Similar steps but navigate to the respective environment directory.

## Remote State (Optional)

To use remote state with GCS:

1. Create a GCS bucket:
   ```bash
   gsutil mb gs://your-terraform-state-bucket
   gsutil versioning set on gs://your-terraform-state-bucket
   ```

2. Uncomment and configure the backend in `main.tf`:
   ```hcl
   backend "gcs" {
     bucket = "your-terraform-state-bucket"
     prefix = "dev/bigtable-pipeline"
   }
   ```

3. Re-initialize:
   ```bash
   terraform init -migrate-state
   ```

## Variables

Key variables (set via `terraform.tfvars` or environment variables):

- `project_id`: Your GCP project ID
- `region`: GCP region (default: us-central1)
- `zone`: GCP zone (default: us-central1-a)

## Outputs

After applying, Terraform will output:
- Bigtable instance name
- Table names
- Network name
- Service account emails

Use these outputs in other tools or scripts.

## Destroying Resources

**⚠️ WARNING: This will delete all resources!**

```bash
terraform destroy
```

Note: Production environments have `deletion_protection = true` to prevent accidental deletion.

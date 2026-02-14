# Terraform Infrastructure

This directory contains Terraform code for provisioning AWS infrastructure.

## Structure

```
terraform/
├── main.tf              # Root module
├── variables.tf         # Variable definitions
├── outputs.tf           # Output values
├── modules/             # Reusable modules
│   ├── vpc/            # VPC and networking
│   ├── s3/             # S3 data lake
│   ├── msk/            # MSK cluster
│   ├── iam/            # IAM roles and policies
│   ├── glue/           # Glue jobs and catalog
│   ├── redshift/       # Redshift cluster
│   └── monitoring/     # CloudWatch alarms
└── environments/       # Environment-specific configs
    ├── dev/
    ├── qa/
    └── prod/
```

## Usage

### Initialize

```bash
terraform init
```

### Select Workspace

```bash
terraform workspace select dev  # or qa, prod
```

### Plan

```bash
terraform plan -var-file="environments/dev/terraform.tfvars"
```

### Apply

```bash
terraform apply -var-file="environments/dev/terraform.tfvars"
```

### Destroy

```bash
terraform destroy -var-file="environments/dev/terraform.tfvars"
```

## Variables

Key variables (set in `environments/{env}/terraform.tfvars`):

- `environment`: Environment name (dev, qa, prod)
- `aws_region`: AWS region
- `vpc_cidr`: VPC CIDR block
- `msk_instance_type`: MSK broker instance type
- `redshift_node_type`: Redshift node type
- `redshift_master_password`: Redshift password (use secrets manager in prod)

## Outputs

After apply, outputs include:

- `s3_datalake_bucket`: S3 bucket name
- `msk_bootstrap_brokers`: MSK endpoint
- `redshift_cluster_endpoint`: Redshift endpoint
- `glue_database_name`: Glue Data Catalog database

## Modules

### VPC Module
- VPC with public/private subnets
- NAT Gateways
- Security groups for MSK, Glue, Redshift
- VPC endpoints for S3 and Glue

### S3 Module
- Data lake bucket with medallion architecture
- Lifecycle policies
- Encryption
- Bucket policies

### MSK Module
- MSK cluster with IAM authentication
- Encryption at rest and in transit
- CloudWatch logging

### Glue Module
- Data Catalog database
- Crawlers for each zone
- Streaming and batch jobs

### Redshift Module
- Redshift cluster
- Subnet group
- Parameter group
- IAM role association

## Backend Configuration

Configure S3 backend in `environments/{env}/backend.tf`:

```hcl
terraform {
  backend "s3" {
    bucket = "terraform-state-{env}"
    key    = "retail-datalake/terraform.tfstate"
    region = "us-east-1"
  }
}
```

## Best Practices

1. Always use workspaces for environment separation
2. Review plan before apply
3. Use remote state (S3 backend)
4. Store secrets in AWS Secrets Manager
5. Tag all resources appropriately
6. Use version constraints for providers


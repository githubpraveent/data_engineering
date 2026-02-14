# Deployment Guide

This guide covers the deployment process for the MongoDB Data Engineering Pipeline.

## Prerequisites

- AWS Account with appropriate permissions
- MongoDB Atlas account
- GitHub repository with Actions enabled
- Terraform >= 1.0
- Ansible >= 2.9
- Python >= 3.9

## GitHub Secrets Configuration

Configure the following secrets in your GitHub repository:

### AWS Secrets
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `AWS_KEY_PAIR_NAME`: EC2 key pair name
- `SSH_PRIVATE_KEY`: Private SSH key for EC2 access
- `TF_STATE_BUCKET`: S3 bucket for Terraform state

### MongoDB Atlas Secrets
- `MONGODB_ATLAS_API_KEY`: MongoDB Atlas API public key
- `MONGODB_ATLAS_API_SECRET`: MongoDB Atlas API private key
- `MONGODB_ATLAS_ORG_ID`: MongoDB Atlas organization ID
- `MONGODB_STAGING_URI`: MongoDB connection string for staging
- `MONGODB_PRODUCTION_URI`: MongoDB connection string for production

### Instance IPs (populated after Terraform)
- `STAGING_PIPELINE_IP_1`: Staging instance IP 1
- `STAGING_PIPELINE_IP_2`: Staging instance IP 2
- `PROD_PIPELINE_IP_1`: Production instance IP 1
- `PROD_PIPELINE_IP_2`: Production instance IP 2

## Deployment Workflow

### 1. Infrastructure Deployment (Terraform)

#### Staging
```bash
cd terraform/environments/staging
terraform init
terraform plan
terraform apply
```

#### Production
```bash
cd terraform/environments/production
terraform init
terraform plan
# Manual approval required
terraform apply
```

### 2. Server Configuration (Ansible)

```bash
cd ansible
ansible-playbook -i inventory/hosts.yml playbooks/site.yml
```

### 3. Application Deployment

```bash
ansible-playbook -i inventory/hosts.yml playbooks/deploy-pipeline.yml
```

## CI/CD Pipeline

### Automatic Workflows

1. **Code Validation**: Runs on every push/PR
   - Linting (Black, Flake8)
   - Type checking (MyPy)
   - Unit tests
   - Terraform validation
   - Ansible syntax check

2. **Terraform Plan**: Runs on PRs and pushes to main/develop
   - Generates infrastructure plan
   - Comments on PRs

3. **Terraform Apply**: 
   - Staging: Automatic on merge to `main`
   - Production: Manual approval required

4. **Ansible Deployment**:
   - Triggered after successful Terraform apply
   - Configures and deploys application

## Manual Deployment

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export MONGODB_URI="mongodb://localhost:27017/test_db"
export ENVIRONMENT="development"

# Run pipeline
python src/pipeline/main.py
```

### Staging Deployment

```bash
# Via GitHub Actions
gh workflow run terraform-apply.yml -f environment=staging -f action=apply

# Or manually
cd terraform/environments/staging
terraform apply -auto-approve
```

### Production Deployment

```bash
# Via GitHub Actions (requires approval)
gh workflow run terraform-apply.yml -f environment=production -f action=apply

# Manual approval required in GitHub UI
```

## Rollback Procedure

### Infrastructure Rollback

```bash
# Revert Terraform state
cd terraform/environments/{environment}
terraform state list
terraform state rm <resource>
terraform apply

# Or revert to previous state
terraform apply -backup=backup.tfstate
```

### Application Rollback

```bash
# Revert to previous version via Ansible
cd ansible
ansible-playbook -i inventory/hosts.yml playbooks/deploy-pipeline.yml \
  -e "deployment_version=<previous_version>"
```

## Monitoring

- CloudWatch Dashboard: Monitor pipeline metrics
- CloudWatch Logs: `/aws/mongodb-pipeline/{environment}/pipeline`
- Alarms: CPU usage, pipeline failures, data quality

## Troubleshooting

### Common Issues

1. **Terraform State Locked**
   ```bash
   terraform force-unlock <lock-id>
   ```

2. **MongoDB Connection Issues**
   - Check IP whitelist in MongoDB Atlas
   - Verify connection string
   - Check VPC peering status

3. **Ansible Connection Issues**
   - Verify SSH key configuration
   - Check security group rules
   - Test SSH connectivity manually

## Security Best Practices

- Never commit secrets to repository
- Use AWS Secrets Manager or Vault for production
- Rotate credentials regularly
- Enable MFA for AWS and MongoDB Atlas
- Restrict network access via security groups
- Use private subnets for compute resources

# Deployment Runbook

## Prerequisites

- AWS CLI configured with appropriate credentials
- Terraform >= 1.0 installed
- Ansible >= 2.9 installed
- Access to GitHub repository
- Required AWS permissions

## Initial Deployment

### 1. Configure Terraform Backend

Edit `terraform/environments/{env}/backend.tf`:

```hcl
terraform {
  backend "s3" {
    bucket = "terraform-state-{env}"
    key    = "retail-datalake/terraform.tfstate"
    region = "us-east-1"
  }
}
```

### 2. Set Environment Variables

```bash
export AWS_REGION=us-east-1
export TF_VAR_redshift_master_password=<secure-password>
```

### 3. Deploy Infrastructure

```bash
cd terraform
terraform init
terraform workspace select dev  # or qa, prod
terraform plan -var-file="environments/dev/terraform.tfvars"
terraform apply -var-file="environments/dev/terraform.tfvars"
```

### 4. Configure Kafka Topics

```bash
cd ansible
export MSK_BOOTSTRAP_SERVERS=<from-terraform-output>
export ENVIRONMENT=dev
ansible-playbook -i inventory/dev.yml playbooks/kafka-setup.yml
```

### 5. Deploy Redshift Schemas

```bash
export REDSHIFT_HOST=<from-terraform-output>
export REDSHIFT_USER=admin
export REDSHIFT_PASSWORD=<password>
ansible-playbook -i inventory/dev.yml playbooks/redshift-setup.yml
```

### 6. Deploy Glue Jobs

Glue jobs are deployed via CI/CD pipeline. Push to the appropriate branch:

```bash
git checkout dev
git push origin dev
```

Or trigger manually via GitHub Actions workflow.

## Updating Deployment

### Infrastructure Changes

1. Make changes to Terraform code
2. Create pull request
3. Review Terraform plan in PR
4. Merge to appropriate branch
5. CI/CD pipeline applies changes

### Glue Job Updates

1. Update Glue job scripts in `glue/`
2. Push to branch (dev/qa/main)
3. CI/CD pipeline uploads scripts to S3
4. Jobs use updated scripts on next run

### Redshift Schema Changes

1. Update SQL scripts in `redshift/`
2. Push to branch
3. CI/CD pipeline runs migrations
4. Verify changes in Redshift

## Rollback Procedures

### Rollback Terraform

```bash
cd terraform
terraform workspace select <env>
terraform state list  # Review current state
terraform state show <resource>  # Check previous version
# Restore from backup or previous commit
git checkout <previous-commit>
terraform apply
```

### Rollback Glue Jobs

1. Go to GitHub Actions
2. Run "Rollback Deployment" workflow
3. Select component: "glue"
4. Specify rollback version/tag
5. Workflow restores previous scripts

### Rollback Redshift

1. Restore from snapshot (if available)
2. Or manually revert SQL changes
3. Run previous schema version scripts

## Verification

After deployment, verify:

1. **Infrastructure**
   ```bash
   terraform output
   ```

2. **Kafka Topics**
   ```bash
   # Use Kafka tools to list topics
   kafka-topics.sh --bootstrap-server <msk-endpoint> --list
   ```

3. **Glue Jobs**
   ```bash
   aws glue list-jobs --region us-east-1
   ```

4. **Redshift**
   ```sql
   SELECT * FROM information_schema.tables 
   WHERE table_schema IN ('staging', 'analytics');
   ```

5. **Run Tests**
   ```bash
   pytest tests/ -v
   ```


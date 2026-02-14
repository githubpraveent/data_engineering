# GitHub Actions Workflows

This directory contains CI/CD workflows for the data pipeline project.

## Workflows

### terraform-validate.yml

Runs on pull requests and pushes to validate Terraform code:
- Terraform format check (`terraform fmt`)
- Terraform validation (`terraform validate`)
- TFLint for linting
- tfsec for security scanning

### terraform-apply.yml

Manually triggered workflow to apply Terraform changes:
- Supports dev, staging, and production environments
- Runs terraform plan first
- Requires manual approval for production
- Automatically runs Ansible playbooks after successful apply

### pipeline-tests.yml

Runs tests for the data pipeline code:
- Python linting (Black, Flake8, Pylint)
- Unit tests with coverage
- Integration tests (only on main branch)
- Data quality check validation

## Required GitHub Secrets

Configure these secrets in your GitHub repository:

- `GCP_PROJECT_ID`: Your GCP project ID
- `GCP_SA_KEY`: Service account key JSON (base64 encoded)
- `GCP_SA_EMAIL`: Service account email
- `BIGTABLE_INSTANCE`: Bigtable instance name (for integration tests)
- `GITHUB_TOKEN`: Automatically provided by GitHub

## Environment Protection

For production environment:
1. Go to Settings → Environments → production
2. Add required reviewers
3. Configure deployment branches

## Usage

### Trigger Terraform Apply

1. Go to Actions tab
2. Select "Terraform Apply"
3. Click "Run workflow"
4. Select environment (dev/staging/production)
5. Optionally enable auto-approve
6. Click "Run workflow"

### View Test Results

- Linting results appear in the workflow run
- Test coverage reports are uploaded to Codecov (if configured)
- Failed tests block merging (if branch protection is enabled)

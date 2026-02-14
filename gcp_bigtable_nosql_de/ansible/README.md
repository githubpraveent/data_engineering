# Ansible Configuration Management

This directory contains Ansible playbooks and roles for configuring the data pipeline infrastructure.

## Structure

```
ansible/
├── playbooks/          # Main playbooks
│   ├── setup.yml      # Infrastructure setup
│   └── deploy-pipeline.yml
├── roles/             # Reusable roles
│   ├── python-runtime/
│   ├── bigtable-client/
│   └── pipeline-service/
└── inventory/         # Inventory files
    ├── dev.yml
    ├── staging.yml
    └── production.yml
```

## Prerequisites

1. Install Ansible >= 2.9:
   ```bash
   pip install ansible
   ```

2. Configure SSH access to target servers

3. Update inventory files with actual host information

## Usage

### Setup Infrastructure

```bash
# Development environment
ansible-playbook -i inventory/dev.yml playbooks/setup.yml

# Staging environment
ansible-playbook -i inventory/staging.yml playbooks/setup.yml

# Production environment
ansible-playbook -i inventory/production.yml playbooks/setup.yml
```

### Deploy Pipeline Service

```bash
ansible-playbook -i inventory/dev.yml playbooks/deploy-pipeline.yml
```

## Variables

Key variables can be set in inventory files or passed via `-e`:

- `gcp_project_id`: GCP project ID
- `bigtable_instance_id`: Bigtable instance name
- `service_account_key_path`: Path to service account key file
- `python_version`: Python version to install (default: 3.9)

## Roles

### python-runtime
Installs Python and required pip packages.

### bigtable-client
Sets up Google Cloud Bigtable client libraries.

### pipeline-service
Deploys the data pipeline as a system service.

## Inventory

Edit inventory files to match your infrastructure:
- Replace `ansible_host` with actual server IPs/hostnames
- Update `gcp_project_id` and `bigtable_instance_id`
- Configure SSH key paths

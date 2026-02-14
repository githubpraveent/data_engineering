# Ansible Configuration Management

This directory contains Ansible playbooks for configuring Kafka topics and Redshift schemas.

## Structure

```
ansible/
├── playbooks/          # Ansible playbooks
│   ├── kafka-setup.yml
│   └── redshift-setup.yml
├── scripts/            # Helper scripts
│   ├── kafka/
│   └── redshift/
└── inventory/         # Environment inventories
    ├── dev.yml
    ├── qa.yml
    └── prod.yml
```

## Prerequisites

- Ansible >= 2.9
- Python 3.8+
- AWS credentials configured
- Access to MSK and Redshift

## Usage

### Setup Kafka Topics

```bash
export MSK_BOOTSTRAP_SERVERS=<msk-endpoint>
export ENVIRONMENT=dev
export AWS_REGION=us-east-1

ansible-playbook -i inventory/dev.yml playbooks/kafka-setup.yml
```

### Setup Redshift Schemas

```bash
export REDSHIFT_HOST=<redshift-endpoint>
export REDSHIFT_PORT=5439
export REDSHIFT_DATABASE=retail_dw
export REDSHIFT_USER=admin
export REDSHIFT_PASSWORD=<password>
export ENVIRONMENT=dev

ansible-playbook -i inventory/dev.yml playbooks/redshift-setup.yml
```

## Playbooks

### kafka-setup.yml

Creates Kafka topics on MSK:
- Validates topic naming
- Creates topics with proper configuration
- Handles existing topics gracefully

### redshift-setup.yml

Sets up Redshift schemas:
- Creates staging and analytics schemas
- Runs DDL scripts
- Grants appropriate permissions

## Scripts

### kafka/create_topics.py

Python script to create Kafka topics using IAM authentication.

### redshift/create_schema.sh

Shell script to create Redshift schemas.

## Inventory

Inventory files define target hosts (localhost for these playbooks).

## Variables

Set via environment variables:
- `MSK_BOOTSTRAP_SERVERS`: MSK endpoint
- `REDSHIFT_HOST`: Redshift endpoint
- `ENVIRONMENT`: Environment name
- `AWS_REGION`: AWS region


# MongoDB NoSQL Data Engineering Pipeline

End-to-end data engineering project with Infrastructure as Code, Configuration Management, CI/CD, and automated data quality.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        GitHub Actions CI/CD                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Validate │  │   Plan   │  │  Deploy  │  │  Monitor │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Terraform (IaC)                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │   VPC    │  │  EC2/ECS │  │ MongoDB  │  │ CloudWatch│        │
│  │          │  │          │  │  Atlas   │  │          │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Ansible (Config Mgmt)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
│  │  Python  │  │ MongoDB  │  │  Agents  │                      │
│  │ Runtime  │  │ Drivers  │  │          │                      │
│  └──────────┘  └──────────┘  └──────────┘                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Pipeline (Python)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Extract  │─▶│ Validate │─▶│Transform │─▶│  Load    │        │
│  │  (CSV)   │  │  (DQ)    │  │ (Agg)    │  │ (MongoDB)│        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MongoDB Collections                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Facts      │  │ Dimensions   │  │ Aggregates   │          │
│  │ (Transactions)│  │ (Products)   │  │ (Daily Stats)│          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
.
├── terraform/
│   ├── modules/
│   │   ├── vpc/
│   │   ├── compute/
│   │   ├── mongodb/
│   │   └── monitoring/
│   ├── environments/
│   │   ├── staging/
│   │   └── production/
│   └── main.tf
├── ansible/
│   ├── roles/
│   │   ├── python/
│   │   ├── mongodb-client/
│   │   └── pipeline-agent/
│   ├── playbooks/
│   │   ├── site.yml
│   │   └── deploy-pipeline.yml
│   └── inventory/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── terraform-plan.yml
│       ├── terraform-apply.yml
│       └── ansible-deploy.yml
├── src/
│   ├── extract/
│   ├── transform/
│   ├── load/
│   ├── quality/
│   └── queries/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── quality/
├── data/
│   └── sample/
├── docs/
└── scripts/
```

## Prerequisites

- Terraform >= 1.0
- Ansible >= 2.9
- Python >= 3.9
- AWS CLI configured
- GitHub Actions enabled
- MongoDB Atlas account (or use local MongoDB for development)

## Quick Start

### 1. Infrastructure Setup

```bash
cd terraform/environments/staging
terraform init
terraform plan
terraform apply
```

### 2. Configuration Management

```bash
cd ansible
ansible-playbook -i inventory/staging playbooks/site.yml
```

### 3. Run Data Pipeline Locally

```bash
pip install -r requirements.txt
export MONGODB_URI="mongodb://localhost:27017"
python src/pipeline/main.py
```

## Environment Variables

Required environment variables (set via GitHub Secrets or `.env`):

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `MONGODB_ATLAS_API_KEY`
- `MONGODB_ATLAS_API_USER`
- `MONGODB_URI`
- `TF_VAR_mongodb_atlas_org_id`

## Deployment Workflow

1. **Development**: Push to `develop` branch triggers validation and staging deployment
2. **Staging**: Automated deployment after merge to `develop`
3. **Production**: Manual approval required after staging validation
4. **Rollback**: Automated rollback via Terraform state management

## Data Quality Checks

- Schema validation (field presence, types)
- Referential integrity
- Duplicate detection
- Null/empty value checks
- Business rule validation

## Monitoring

- CloudWatch metrics for pipeline execution
- Error logging and alerting
- Data quality dashboards
- Performance metrics

## License

MIT

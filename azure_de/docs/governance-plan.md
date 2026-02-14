# Data Governance Plan

## Table of Contents
1. [Overview](#overview)
2. [Data Catalog and Lineage](#data-catalog-and-lineage)
3. [Access Control](#access-control)
4. [Data Classification](#data-classification)
5. [Schema Management](#schema-management)
6. [Data Quality Standards](#data-quality-standards)
7. [Compliance and Auditing](#compliance-and-auditing)

## Overview

This governance plan establishes policies and procedures for managing data assets across the Azure Retail Data Lake and Data Warehouse. It ensures data quality, security, compliance, and proper usage.

## Data Catalog and Lineage

### Azure Purview Integration

#### Data Sources Registered
- **ADLS Gen2**: Bronze, Silver, Gold containers
- **Azure Synapse Analytics**: SQL Pool databases
- **Azure Databricks**: Delta Lake tables
- **Azure Event Hubs**: Event streams
- **Azure Data Factory**: Pipelines

#### Scanning Schedule
- **ADLS**: Daily scan for new files and schema changes
- **Synapse**: Weekly scan for schema changes
- **Databricks**: Weekly scan for new tables
- **ADF**: On-demand scan after pipeline changes

#### Lineage Tracking
- **Source Systems** → **Bronze Layer**
- **Bronze Layer** → **Silver Layer** (via Databricks)
- **Silver Layer** → **Gold Layer** (via Databricks)
- **Gold Layer** → **Data Warehouse** (via Synapse)
- **Data Warehouse** → **Reports/Analytics**

### Business Glossary

#### Key Terms
- **Customer**: Individual who purchases products
- **Transaction**: Single purchase event
- **Order**: Collection of transactions
- **Product**: Item sold in stores
- **Store**: Physical retail location
- **Rewards Points**: Customer loyalty program points

#### Data Dictionary
- Maintained in Purview
- Updated when new sources are onboarded
- Reviewed quarterly

## Access Control

### Role-Based Access Control (RBAC)

#### Azure AD Groups

**Data Engineers**
- Full access to all resources
- Can modify pipelines, notebooks, DAGs
- Can update schemas and stored procedures

**Data Analysts**
- Read access to Gold layer and Data Warehouse
- Can query Synapse SQL Pool
- Can access Databricks for ad-hoc analysis

**Data Scientists**
- Read access to Silver and Gold layers
- Can create Databricks notebooks
- Can access Synapse for ML workloads

**Business Users**
- Read-only access to Data Warehouse
- Can run reports and queries
- No access to raw data layers

#### Resource-Level Permissions

**ADLS Gen2**
```bash
# Data Engineers: Storage Blob Data Contributor
# Data Analysts: Storage Blob Data Reader (Gold container only)
# Data Scientists: Storage Blob Data Reader (Silver, Gold containers)
```

**Databricks**
- Workspace Admin: Data Engineers
- Users: Data Analysts, Data Scientists
- Can View: Business Users (read-only)

**Synapse Analytics**
```sql
-- Data Engineers: db_owner
-- Data Analysts: db_datareader, db_datawriter (staging schema)
-- Data Scientists: db_datareader
-- Business Users: db_datareader (dwh schema only)
```

### Service Principal Management

#### Service Principals Used
- **Databricks**: Access to ADLS, Event Hubs
- **ADF**: Access to source systems, ADLS
- **Synapse**: Access to ADLS
- **Airflow**: Access to Azure services

#### Secret Rotation
- Rotate every 90 days
- Store in Azure Key Vault
- Update service connections after rotation

## Data Classification

### Classification Levels

#### Public
- Aggregated, anonymized data
- No PII or sensitive information
- Example: Store-level sales summaries

#### Internal
- Business data, no PII
- Example: Product catalog, store locations

#### Confidential
- Contains business-sensitive information
- Example: Sales transactions, inventory levels

#### Highly Confidential
- Contains PII or sensitive customer data
- Example: Customer details, payment information
- Requires encryption at rest and in transit

### Classification Process

1. **Automated Classification**
   - Purview automatically classifies data based on patterns
   - Identifies PII (SSN, credit card numbers, etc.)

2. **Manual Review**
   - Data stewards review classifications
   - Adjust classifications as needed

3. **Labeling**
   - Apply sensitivity labels in Purview
   - Enforce access policies based on labels

## Schema Management

### Schema Change Process

#### Development
1. Developer creates schema change in dev environment
2. Document change in pull request
3. Review by data engineering team

#### Testing
1. Deploy to QA environment
2. Run integration tests
3. Validate data quality

#### Production
1. Deploy via CI/CD pipeline
2. Monitor for issues
3. Update Purview catalog

### Schema Evolution

#### Delta Lake Schema Evolution
```python
# Automatic schema evolution (enabled in Databricks)
spark.conf.set("spark.databricks.delta.schema.autoMerge.enabled", "true")

# Manual schema evolution
df.write.format("delta").mode("overwrite").option("mergeSchema", "true").save(path)
```

#### Synapse Schema Changes
```sql
-- Add new column
ALTER TABLE dwh.fact_sales ADD new_column INT NULL;

-- Update statistics after schema change
UPDATE STATISTICS dwh.fact_sales;
```

### Schema Versioning
- Track schema versions in Git
- Document breaking changes
- Maintain backward compatibility when possible

## Data Quality Standards

### Quality Dimensions

#### Completeness
- **Target**: >95% for critical fields
- **Measurement**: Count of null values
- **Action**: Alert if completeness drops below threshold

#### Accuracy
- **Target**: 100% for key fields (IDs, amounts)
- **Measurement**: Validation against business rules
- **Action**: Reject records that fail validation

#### Consistency
- **Target**: Consistent formats across sources
- **Measurement**: Format validation, cross-source comparison
- **Action**: Standardize formats in transformation layer

#### Timeliness
- **Target**: Data available within SLA
  - Real-time: <5 minutes latency
  - Batch: Within 2 hours of source update
- **Measurement**: Time from source to warehouse
- **Action**: Alert if SLA not met

#### Validity
- **Target**: 100% valid records
- **Measurement**: Schema validation, data type checks
- **Action**: Reject invalid records, log for review

### Quality Checks

#### Automated Checks
- **Bronze Layer**: Schema validation, completeness
- **Silver Layer**: Business rule validation, deduplication
- **Gold Layer**: Referential integrity, calculated fields
- **Warehouse**: Foreign key constraints, data type validation

#### Manual Reviews
- Quarterly data quality audits
- Review of quality metrics
- Investigation of quality issues

### Quality Monitoring

#### Dashboards
- Azure Monitor dashboards for quality metrics
- Airflow DAG success/failure rates
- Data quality test results

#### Alerts
- Email/Slack on quality failures
- PagerDuty for critical issues
- Daily quality summary reports

## Compliance and Auditing

### Data Retention

#### Retention Policies
- **Bronze**: 90 days (Hot/Cool), then Archive
- **Silver**: 180 days (Hot/Cool), then Archive
- **Gold**: 365 days (Hot/Cool), then Archive
- **Warehouse**: Indefinite (all historical data)

#### Deletion Process
1. Review data for legal/compliance requirements
2. Archive before deletion
3. Document deletion in audit log
4. Verify deletion completion

### Audit Logging

#### Logged Activities
- Data access (who, what, when)
- Schema changes
- Pipeline executions
- Access grant/revoke
- Data quality failures

#### Log Storage
- Azure Monitor Log Analytics
- Retention: 90 days (standard), 1 year (compliance)
- Regular review of audit logs

### Compliance Requirements

#### GDPR (if applicable)
- Right to access: Provide customer data on request
- Right to deletion: Delete customer data on request
- Data minimization: Only collect necessary data
- Consent management: Track customer consent

#### Industry Standards
- PCI DSS: For payment card data (if applicable)
- HIPAA: For health data (if applicable)
- SOX: For financial reporting data

### Data Privacy

#### PII Handling
- Encrypt PII at rest and in transit
- Limit access to PII
- Anonymize/Pseudonymize for analytics
- Document PII usage

#### Data Anonymization
- Remove direct identifiers
- Generalize sensitive attributes
- Use k-anonymity for published datasets

## Data Stewardship

### Roles and Responsibilities

#### Data Stewards
- Own data quality for their domain
- Review and approve schema changes
- Resolve data quality issues
- Maintain business glossary

#### Data Engineers
- Implement data pipelines
- Maintain infrastructure
- Monitor data quality
- Respond to incidents

#### Data Governance Team
- Define governance policies
- Review compliance
- Manage access controls
- Coordinate with stakeholders

### Governance Meetings

#### Weekly
- Data quality review
- Incident review
- Pipeline status

#### Monthly
- Schema change review
- Access review
- Compliance check

#### Quarterly
- Governance policy review
- Data retention review
- Audit log review

## Best Practices

### Data Management
1. **Document Everything**: Schemas, transformations, business rules
2. **Version Control**: All code and schemas in Git
3. **Test Before Deploy**: Unit tests, integration tests, quality checks
4. **Monitor Continuously**: Set up alerts and dashboards
5. **Review Regularly**: Quality metrics, access controls, compliance

### Security
1. **Least Privilege**: Grant minimum necessary access
2. **Encryption**: Encrypt sensitive data at rest and in transit
3. **Secrets Management**: Use Key Vault for all secrets
4. **Network Security**: Use private endpoints where possible
5. **Regular Audits**: Review access and activities regularly

### Quality
1. **Fail Fast**: Reject bad data early in pipeline
2. **Validate Often**: Quality checks at each layer
3. **Monitor Metrics**: Track quality metrics over time
4. **Continuous Improvement**: Address quality issues promptly

## Tools and Resources

### Azure Purview
- Data catalog and lineage
- Data classification
- Access policies

### Azure Monitor
- Metrics and logs
- Alerts and dashboards
- Performance monitoring

### Azure Key Vault
- Secret management
- Certificate management
- Access policies

### Git/GitHub
- Version control
- Code review
- CI/CD pipelines

## Contact

For governance questions or issues:
- **Data Governance Team**: data-governance@company.com
- **Data Stewards**: See Purview for domain-specific stewards
- **Security Team**: security@company.com


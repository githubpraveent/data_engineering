# Operational Runbook

## Table of Contents
1. [Overview](#overview)
2. [Alerting and Failure Recovery](#alerting-and-failure-recovery)
3. [Capacity Planning](#capacity-planning)
4. [Data Retention Policy](#data-retention-policy)
5. [Security and Access Management](#security-and-access-management)
6. [Troubleshooting](#troubleshooting)

## Overview

This runbook provides operational procedures for the Azure Retail Data Lake and Data Warehouse solution. It covers common operational tasks, failure recovery, and maintenance procedures.

## Alerting and Failure Recovery

### Airflow DAG Failures

#### Symptoms
- DAG task shows as "Failed" in Airflow UI
- Email/Slack notification received
- Logs show error messages

#### Recovery Steps

1. **Check Airflow Logs**
   ```bash
   # Access Airflow pod in AKS
   kubectl exec -it <airflow-pod> -n <namespace> -- bash
   # View logs
   airflow tasks logs <dag_id> <task_id> <execution_date>
   ```

2. **Identify Failure Type**
   - **Databricks Job Failure**: Check Databricks workspace for job logs
   - **ADF Pipeline Failure**: Check Azure Data Factory monitoring
   - **Synapse Query Failure**: Check Synapse query history
   - **Connection Issues**: Verify service principal credentials

3. **Retry Failed Task**
   ```bash
   # Via Airflow UI: Click "Clear" on failed task, then "Trigger DAG"
   # Or via CLI:
   airflow tasks clear <dag_id> <task_id> --start-date <date> --end-date <date>
   ```

4. **Manual Recovery**
   - For data ingestion failures: Re-run ingestion DAG for specific date range
   - For transformation failures: Re-run transformation DAG after fixing data issues
   - For warehouse load failures: Re-run dimension/fact load procedures

### Databricks Job Failures

#### Symptoms
- Job shows as "Failed" in Databricks UI
- Airflow task fails with Databricks error
- Cluster terminates unexpectedly

#### Recovery Steps

1. **Check Job Logs**
   - Navigate to Databricks Workspace → Jobs → Select failed job → View logs

2. **Common Issues and Solutions**
   - **Out of Memory**: Increase cluster size or optimize Spark configuration
   - **Timeout**: Increase job timeout or optimize query performance
   - **Connection Issues**: Verify ADLS/Event Hubs connection strings in Key Vault
   - **Schema Mismatch**: Check Delta Lake schema evolution settings

3. **Restart Job**
   ```python
   # Via Databricks API or UI
   # Or re-trigger via Airflow DAG
   ```

### Synapse Query Failures

#### Symptoms
- Stored procedure execution fails
- Query timeout errors
- Resource limit exceeded

#### Recovery Steps

1. **Check Query History**
   ```sql
   SELECT * FROM sys.dm_pdw_exec_requests
   WHERE status = 'Failed'
   ORDER BY submit_time DESC
   ```

2. **Common Issues**
   - **DWU Limit**: Scale up SQL Pool temporarily
   - **Query Timeout**: Optimize query or increase timeout
   - **Deadlock**: Review transaction isolation levels

3. **Retry Procedure**
   ```sql
   -- Re-run failed stored procedure
   EXEC dwh.sp_load_customer_dimension @processing_date = '2024-01-15'
   ```

### Event Hubs Throughput Issues

#### Symptoms
- High latency in event processing
- Backlog of unprocessed events
- Throughput unit limit reached

#### Recovery Steps

1. **Monitor Metrics**
   - Azure Portal → Event Hubs → Metrics
   - Check: Incoming Messages, Outgoing Messages, Throttled Requests

2. **Scale Up**
   ```bash
   az eventhubs namespace update \
     --name <namespace> \
     --resource-group <rg> \
     --capacity <new_capacity>
   ```

3. **Enable Auto-Inflate**
   - Already configured in Terraform
   - Verify auto-inflate is enabled in Azure Portal

## Capacity Planning

### Databricks Clusters

#### Scaling Strategy
- **Standard Clusters**: Auto-scale between 1-4 nodes for batch jobs
- **High Concurrency Clusters**: Auto-scale between 2-8 nodes for interactive
- **Job Clusters**: Auto-terminate after job completion

#### Cost Optimization
- Use spot instances for non-critical workloads
- Enable auto-termination (20-30 minutes idle)
- Right-size clusters based on workload patterns

#### Monitoring
```python
# Check cluster utilization
# Databricks UI → Clusters → Select cluster → Metrics
```

### Synapse SQL Pool

#### Scaling Strategy
- **Dev**: DW100c (can pause when not in use)
- **QA**: DW200c
- **Prod**: DW500c (or higher based on workload)

#### Auto-Pause Configuration
- Pause after 15 minutes of inactivity
- Resume automatically on query submission

#### Performance Tuning
```sql
-- Check query performance
SELECT * FROM sys.dm_pdw_exec_requests
WHERE status = 'Running'
ORDER BY submit_time DESC

-- Analyze table statistics
DBCC SHOW_STATISTICS('dwh.fact_sales', 'PK_fact_sales')
```

### Event Hubs

#### Throughput Units
- **Dev**: 1 TU
- **QA**: 2 TU
- **Prod**: 4-10 TU (with auto-inflate to 20)

#### Monitoring
- Track: Incoming/Outgoing messages per second
- Alert on: Throttled requests > 0

### ADLS Gen2 Storage

#### Lifecycle Management
- **Hot Tier**: 0-30 days (frequently accessed)
- **Cool Tier**: 30-90 days (infrequently accessed)
- **Archive Tier**: >90 days (rarely accessed)

#### Cost Optimization
- Enable lifecycle policies (configured in Terraform)
- Use appropriate access tiers
- Archive old Bronze data after 90 days

## Data Retention Policy

### Bronze Layer (Raw Data)
- **Retention**: 90 days in Hot/Cool tier
- **Archive**: After 90 days, move to Archive tier
- **Deletion**: After 365 days, delete (configurable)

### Silver Layer (Staged Data)
- **Retention**: 180 days in Hot/Cool tier
- **Archive**: After 180 days, move to Archive tier
- **Deletion**: After 730 days (2 years)

### Gold Layer (Curated Data)
- **Retention**: 365 days in Hot/Cool tier
- **Archive**: After 365 days, move to Archive tier
- **Deletion**: After 1095 days (3 years)

### Data Warehouse (Synapse)
- **Fact Tables**: Retain all historical data
- **Dimension Tables**: Retain all versions (SCD Type 2)
- **Staging Tables**: Truncate after successful load (daily)

### Implementation
```sql
-- Example: Archive old Bronze data
-- Run via ADF pipeline or Databricks job
-- Move data from Hot/Cool to Archive tier based on lifecycle policy
```

## Security and Access Management

### Granting Access

#### ADLS Access
```bash
# Grant Storage Blob Data Contributor role
az role assignment create \
  --role "Storage Blob Data Contributor" \
  --assignee <user-principal-name> \
  --scope /subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.Storage/storageAccounts/<storage-account>
```

#### Databricks Access
1. Add user to Azure AD
2. Assign to Databricks workspace via Azure Portal
3. Configure workspace-level permissions in Databricks

#### Synapse Access
```sql
-- Grant database access
CREATE USER [user@domain.com] FROM EXTERNAL PROVIDER;
ALTER ROLE db_datareader ADD MEMBER [user@domain.com];
ALTER ROLE db_datawriter ADD MEMBER [user@domain.com];
```

### Revoking Access
```bash
# Remove role assignment
az role assignment delete \
  --assignee <user-principal-name> \
  --role "Storage Blob Data Contributor" \
  --scope <resource-scope>
```

### Managing Secrets

#### Key Vault Access
```bash
# Grant Key Vault access
az keyvault set-policy \
  --name <key-vault-name> \
  --upn <user@domain.com> \
  --secret-permissions get list
```

#### Rotating Secrets
1. Generate new secret in Key Vault
2. Update service connections (Databricks, ADF, Synapse)
3. Test connections
4. Remove old secret version

### Schema Changes

#### Process for Schema Changes
1. **Development**: Make changes in dev environment
2. **Testing**: Validate in QA environment
3. **Approval**: Get approval from data governance team
4. **Deployment**: Deploy via CI/CD pipeline to production
5. **Documentation**: Update Purview data catalog

#### Delta Lake Schema Evolution
```python
# Enable schema evolution in Databricks
spark.conf.set("spark.databricks.delta.schema.autoMerge.enabled", "true")
```

## Troubleshooting

### Common Issues

#### Issue: Airflow DAG Not Running
**Solution**:
1. Check DAG is enabled in Airflow UI
2. Verify schedule_interval is correct
3. Check Airflow scheduler is running
4. Review DAG syntax for errors

#### Issue: Databricks Cluster Not Starting
**Solution**:
1. Check cluster configuration
2. Verify service principal has permissions
3. Check quota limits in Azure subscription
4. Review cluster logs for errors

#### Issue: Synapse Query Slow
**Solution**:
1. Check DWU utilization
2. Review query execution plan
3. Verify statistics are up to date
4. Consider scaling up SQL Pool

#### Issue: Event Hubs Messages Not Processing
**Solution**:
1. Check consumer group offset
2. Verify Databricks streaming job is running
3. Check Event Hubs throughput limits
4. Review checkpoint location in ADLS

### Monitoring and Logging

#### Azure Monitor
- **Metrics**: Track service health and performance
- **Logs**: Query Log Analytics for detailed logs
- **Alerts**: Configure alerts for failures and thresholds

#### Key Metrics to Monitor
- Airflow: DAG success rate, task duration
- Databricks: Job success rate, cluster utilization
- Synapse: Query performance, DWU utilization
- Event Hubs: Throughput, latency, throttled requests
- ADLS: Storage usage, request rates

### Support Contacts
- **Data Engineering Team**: data-engineering@company.com
- **Azure Support**: Via Azure Portal
- **On-Call**: PagerDuty rotation


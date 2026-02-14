# Operational Runbook

## Monitoring

### CloudWatch Dashboards

- **MSK Metrics**: Consumer lag, throughput, errors
- **Glue Metrics**: Job success/failure, duration
- **Redshift Metrics**: CPU, storage, query performance
- **S3 Metrics**: Request counts, data transfer

### Key Metrics to Monitor

1. **MSK Consumer Lag**: Should be < 10,000 messages
2. **Glue Job Success Rate**: Should be > 99%
3. **Redshift CPU**: Should be < 80%
4. **Data Freshness**: Landing zone should have data within last hour

### Alarms

CloudWatch alarms are configured for:
- MSK consumer lag > 10,000
- Glue job failures
- Redshift CPU > 80%

## Common Issues and Resolutions

### MSK Consumer Lag High

**Symptoms**: Consumer lag increasing, data delay

**Resolution**:
1. Check Glue streaming job status
2. Increase Glue worker count
3. Check MSK broker health
4. Review partition count

```bash
# Check Glue job status
aws glue get-job --job-name <job-name>

# Increase workers
aws glue update-job --job-name <job-name> --job-update '{"NumberOfWorkers": 4}'
```

### Glue Job Failures

**Symptoms**: Jobs failing, errors in CloudWatch logs

**Resolution**:
1. Check CloudWatch logs: `/aws-glue/jobs/<job-name>`
2. Review error messages
3. Check S3 permissions
4. Verify MSK connectivity
5. Restart job if transient error

```bash
# View recent job runs
aws glue get-job-runs --job-name <job-name> --max-results 10

# Check logs
aws logs tail /aws-glue/jobs/<job-name> --follow
```

### Redshift Performance Issues

**Symptoms**: Slow queries, high CPU

**Resolution**:
1. Check query queue
2. Review WLM (Workload Management) settings
3. Analyze tables
4. Consider resizing cluster

```sql
-- Check query queue
SELECT * FROM stv_recents;

-- Analyze tables
ANALYZE analytics.fact_sales;
ANALYZE analytics.dim_customer;
```

### Data Quality Issues

**Symptoms**: Invalid data, missing records

**Resolution**:
1. Check staging zone data quality flags
2. Review validation rules in Glue jobs
3. Check source data
4. Re-run batch jobs if needed

```bash
# Check S3 data
aws s3 ls s3://retail-datalake-<env>/staging/ --recursive

# Re-run batch job
aws glue start-job-run --job-name <batch-job-name>
```

## Scaling

### Scale MSK

```bash
# Update broker count in Terraform
# Then apply
terraform apply
```

### Scale Glue Jobs

```bash
# Update worker count
aws glue update-job \
  --job-name <job-name> \
  --job-update '{"NumberOfWorkers": 8, "WorkerType": "G.2X"}'
```

### Scale Redshift

```bash
# Resize cluster
aws redshift modify-cluster \
  --cluster-identifier <cluster-id> \
  --node-type <new-node-type> \
  --number-of-nodes <new-count>
```

## Maintenance

### Regular Tasks

1. **Weekly**: Review CloudWatch metrics and alarms
2. **Monthly**: Analyze Redshift query performance
3. **Quarterly**: Review and optimize S3 lifecycle policies
4. **As needed**: Update Glue job scripts, Redshift schemas

### Backup and Recovery

- **Redshift**: Automated snapshots (7-day retention)
- **S3**: Versioning enabled (prod), lifecycle policies
- **Terraform State**: Stored in S3 backend

### Onboarding New Source Tables

1. Create Kafka topic (via Ansible)
2. Add Glue streaming job
3. Create Redshift staging table
4. Add SCD/fact processing
5. Update tests
6. Deploy via CI/CD

See `docs/runbooks/onboarding-new-tables.md` for details.

## Emergency Procedures

### Service Outage

1. Check CloudWatch dashboards
2. Review recent deployments
3. Check AWS Service Health Dashboard
4. Rollback if recent deployment issue
5. Escalate to AWS Support if needed

### Data Corruption

1. Stop affected jobs
2. Identify corrupted data range
3. Restore from backup/snapshot
4. Re-process affected time period
5. Verify data quality
6. Resume normal operations

### Security Incident

1. Rotate credentials immediately
2. Review CloudTrail logs
3. Check IAM policies
4. Revoke unauthorized access
5. Update security groups if needed


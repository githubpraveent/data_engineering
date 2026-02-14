# Onboarding New Source Tables

This runbook describes how to add a new source table to the data pipeline.

## Prerequisites

- Access to source table schema
- Understanding of table's business purpose
- Decision on SCD type (Type 1 or Type 2)

## Steps

### 1. Create Kafka Topic

Edit `ansible/playbooks/kafka-setup.yml` and add new topic:

```yaml
- name: retail.new_table.cdc
  partitions: 3
  replication_factor: 3
  config:
    retention.ms: 604800000
    compression.type: snappy
```

Run Ansible playbook:
```bash
ansible-playbook -i inventory/<env>.yml playbooks/kafka-setup.yml
```

### 2. Create Glue Streaming Job

Create new file `glue/streaming/new_table_streaming.py`:

```python
# Copy from customer_streaming.py and modify:
# - Topic name
# - Schema definition
# - Table name in metadata
```

Update Terraform `terraform/modules/glue/main.tf`:

```hcl
resource "aws_glue_job" "streaming_new_table" {
  # Similar to existing streaming jobs
  # Update topic name and script location
}
```

### 3. Create Redshift Staging Table

Add to `redshift/schemas/staging.sql`:

```sql
CREATE TABLE IF NOT EXISTS staging.new_table_streaming (
    -- Define columns based on source table
    ...
);
```

### 4. Create Dimension or Fact Processing

**For Dimension (SCD Type 1)**:
- Copy `redshift/scd/scd_type1_product.sql`
- Modify for new table
- Add to `redshift/scd/`

**For Dimension (SCD Type 2)**:
- Copy `redshift/scd/scd_type2_customer.sql`
- Modify for new table
- Add to `redshift/scd/`

**For Fact Table**:
- Add to `redshift/facts/load_sales_fact.sql` or create new procedure

### 5. Update Batch Jobs

Update `glue/batch/landing_to_staging.py`:
- Add validation function for new table
- Add to processing logic

Update `glue/batch/staging_to_curated.py`:
- Add transformation logic for new table

### 6. Update Tests

Add tests in:
- `tests/kafka/test_topic_validation.py`
- `tests/glue/test_etl_transformations.py`
- `tests/redshift/test_data_quality.py`

### 7. Deploy

1. Commit changes to feature branch
2. Create pull request
3. Review and merge
4. CI/CD pipeline deploys changes
5. Verify in target environment

### 8. Verification

1. **Kafka**: Verify topic exists and receives messages
2. **S3**: Check landing zone has data
3. **Glue**: Verify streaming job runs successfully
4. **Redshift**: Verify staging table has data
5. **Analytics**: Verify dimension/fact tables populated

```bash
# Check Kafka topic
kafka-console-consumer.sh --bootstrap-server <msk-endpoint> \
  --topic retail.new_table.cdc --from-beginning

# Check S3
aws s3 ls s3://retail-datalake-<env>/landing/new_table/

# Check Redshift
psql -h <redshift-endpoint> -U admin -d retail_dw -c \
  "SELECT COUNT(*) FROM staging.new_table_streaming;"
```

## Example: Adding Product Table

### 1. Kafka Topic
```yaml
- name: retail.product.cdc
  partitions: 3
  replication_factor: 3
```

### 2. Glue Streaming
- File: `glue/streaming/product_streaming.py`
- Topic: `retail.product.cdc`
- S3 path: `s3://retail-datalake-<env>/landing/product/`

### 3. Redshift Staging
```sql
CREATE TABLE staging.product_streaming (
    product_id INTEGER,
    product_name VARCHAR(255),
    category VARCHAR(100),
    price DECIMAL(10, 2),
    ...
);
```

### 4. SCD Type 1 Dimension
- File: `redshift/scd/scd_type1_product.sql`
- Table: `analytics.dim_product`

### 5. Tests
- Add product schema validation
- Add product transformation tests
- Add product dimension tests

## Checklist

- [ ] Kafka topic created
- [ ] Glue streaming job created and deployed
- [ ] Redshift staging table created
- [ ] SCD/fact procedure created
- [ ] Batch jobs updated
- [ ] Tests added and passing
- [ ] Documentation updated
- [ ] Deployed to dev environment
- [ ] Verified in dev
- [ ] Deployed to qa/prod
- [ ] Production monitoring configured


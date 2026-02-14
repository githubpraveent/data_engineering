# Dagster Orchestration Guide

## Overview

This project includes Dagster as an alternative orchestration platform alongside Airflow. Dagster provides a modern, code-first approach to data orchestration with strong typing, asset-based modeling, and excellent developer experience.

## Why Dagster?

- **Asset-Based Modeling**: Data assets are first-class citizens, making data lineage explicit
- **Type Safety**: Strong typing helps catch errors early
- **Developer Experience**: Better IDE support, clearer code structure
- **Observability**: Built-in metadata tracking and visualization
- **Testing**: Easier to test data pipelines with Dagster's testing framework

## Architecture

Dagster organizes the pipeline into:

1. **Assets**: Represent data products (tables, views, files)
   - Bronze assets: `raw_pos_data`, `raw_orders_data`, `raw_inventory_data`
   - Silver assets: `stg_pos_data`, `stg_orders_data`, `stg_inventory_data`
   - Gold assets: `dim_customer`, `dim_product`, `fact_sales`

2. **Jobs**: Orchestrate operations
   - `ingestion_job`: Data ingestion pipeline
   - `transformation_job`: Bronze → Silver → Gold transformations
   - `data_quality_job`: Data quality monitoring

3. **Schedules**: Automate job execution
   - Ingestion: Every hour
   - Transformation: Every hour
   - Data Quality: Every 6 hours

## Setup

### 1. Install Dependencies

```bash
./scripts/setup_dagster.sh
```

Or manually:
```bash
pip install dagster==1.5.0 dagster-snowflake==0.21.0 dagster-webserver==1.5.0
```

### 2. Configure Environment Variables

```bash
export SNOWFLAKE_ACCOUNT=your_account
export SNOWFLAKE_USER=your_user
export SNOWFLAKE_PASSWORD=your_password
export SNOWFLAKE_WAREHOUSE=WH_TRANS
export SNOWFLAKE_DATABASE=DEV_RAW
export SNOWFLAKE_SCHEMA=BRONZE
export ENVIRONMENT=DEV
```

### 3. Start Dagster

**Development Mode:**
```bash
dagster dev -f dagster/definitions.py
```

This starts:
- Dagster UI at http://localhost:3000
- Code server for hot reloading
- Scheduler for running jobs

**Production Deployment:**
- Use Dagster Cloud for managed deployment
- Or deploy Dagster on your infrastructure (Kubernetes, Docker, etc.)

## Using Dagster

### Viewing Assets

1. Open Dagster UI: http://localhost:3000
2. Navigate to "Assets" tab
3. View asset graph showing dependencies
4. Click on assets to see metadata, materialization history

### Running Jobs

**Via UI:**
1. Go to "Jobs" tab
2. Select a job (e.g., `ingestion_job`)
3. Click "Launch Run"
4. Monitor execution in real-time

**Via CLI:**
```bash
dagster job execute -f dagster/definitions.py -j ingestion_job
```

**Via Python:**
```python
from dagster import DagsterInstance
from dagster.definitions import ingestion_job

instance = DagsterInstance.ephemeral()
result = ingestion_job.execute_in_process(instance=instance)
```

### Materializing Assets

**Materialize specific assets:**
```bash
dagster asset materialize -f dagster/definitions.py -s raw_pos_data
```

**Materialize asset and dependencies:**
```bash
dagster asset materialize -f dagster/definitions.py -s fact_sales --select-all
```

**Via UI:**
1. Go to "Assets" tab
2. Select assets to materialize
3. Click "Materialize"

### Schedules

Schedules are automatically created and can be:
- **Enabled/Disabled** via UI or CLI
- **Modified** by updating schedule definitions
- **Monitored** in the "Schedules" tab

**Enable a schedule:**
```bash
dagster schedule up -f dagster/definitions.py -n ingestion_schedule
```

**Pause a schedule:**
```bash
dagster schedule stop -f dagster/definitions.py -n ingestion_schedule
```

## Asset Definitions

### Bronze Assets

```python
@asset(
    group_name="bronze",
    description="Raw POS transaction data from source system"
)
def raw_pos_data(context: AssetExecutionContext, snowflake: SnowflakeResource) -> Dict[str, Any]:
    """Asset representing raw POS data in Bronze layer"""
    # Implementation checks row count and latest load
    # Returns metadata about the asset
```

### Silver Assets

```python
@asset(
    group_name="silver",
    deps=[raw_pos_data],  # Depends on bronze asset
    description="Cleaned and validated POS staging data"
)
def stg_pos_data(context: AssetExecutionContext, snowflake: SnowflakeResource) -> Dict[str, Any]:
    """Asset representing cleaned POS data in Silver layer"""
    # Executes transformation task
    # Validates data quality
    # Returns quality metrics
```

### Gold Assets

```python
@asset(
    group_name="gold_facts",
    deps=[dim_customer, dim_product, stg_pos_data],  # Multiple dependencies
    description="Sales fact table with dimension lookups"
)
def fact_sales(context: AssetExecutionContext, snowflake: SnowflakeResource) -> Dict[str, Any]:
    """Asset representing sales fact table in Gold layer"""
    # Loads fact table
    # Returns summary statistics
```

## Job Definitions

### Ingestion Job

```python
@job(
    description="Ingest retail data from source systems into Snowflake",
    tags={"orchestrator": "dagster", "layer": "ingestion"}
)
def ingestion_job():
    """Job definition for data ingestion pipeline"""
    pipe_status = check_snowpipe_status()
    validation = validate_ingestion(pipe_status)
    data_quality_checks(validation)
```

### Transformation Job

```python
@job(
    description="Transform retail data from Bronze to Silver to Gold layers",
    tags={"orchestrator": "dagster", "layer": "transformation"}
)
def transformation_job():
    """Job definition for data transformation pipeline"""
    # Parallel transformations
    pos_result = transform_pos()
    orders_result = transform_orders()
    inventory_result = transform_inventory()
    
    # Sequential validations and loads
    silver_validation = validate_silver_quality(...)
    customer_dim = load_dim_customer()
    product_dim = load_dim_product()
    fact_sales_result = load_fact_sales(...)
    validate_gold_quality(facts=fact_sales_result)
```

## Monitoring and Observability

### Asset Lineage

Dagster automatically tracks:
- **Upstream dependencies**: What assets this asset depends on
- **Downstream dependencies**: What assets depend on this asset
- **Materialization history**: When and how assets were materialized
- **Metadata**: Custom metadata added by assets

### Run History

View:
- **Run status**: Success, failure, in-progress
- **Execution logs**: Detailed logs from each op
- **Timing**: How long each op took
- **Resource usage**: Snowflake warehouse usage

### Alerts

Configure alerts for:
- Failed runs
- Stale assets (not materialized recently)
- Data quality failures
- Performance degradation

## Testing

### Testing Assets

```python
from dagster import build_op_context
from dagster.assets import raw_pos_data
from dagster_snowflake import SnowflakeResource

def test_raw_pos_data():
    # Mock Snowflake resource
    snowflake = SnowflakeResource(...)
    
    # Build context
    context = build_op_context(resources={"snowflake": snowflake})
    
    # Execute asset
    result = raw_pos_data(context, snowflake)
    
    # Assert results
    assert result["status"] == "success"
    assert result["row_count"] > 0
```

### Testing Jobs

```python
from dagster import DagsterInstance
from dagster.jobs.ingestion_job import ingestion_job

def test_ingestion_job():
    instance = DagsterInstance.ephemeral()
    result = ingestion_job.execute_in_process(instance=instance)
    assert result.success
```

## Comparison: Airflow vs Dagster

| Feature | Airflow | Dagster |
|---------|---------|---------|
| **Model** | Task-based | Asset-based |
| **Type Safety** | Limited | Strong typing |
| **Lineage** | Manual tracking | Automatic |
| **UI** | Web UI | Modern UI with asset graph |
| **Testing** | Requires setup | Built-in testing framework |
| **Scheduling** | Cron-based | Cron + asset freshness |
| **Observability** | Good | Excellent (built-in metadata) |
| **Learning Curve** | Moderate | Steeper (but more powerful) |

## Migration from Airflow

If you're currently using Airflow and want to migrate:

1. **Start with Assets**: Convert Airflow tasks to Dagster assets
2. **Create Jobs**: Group related assets into jobs
3. **Set Up Schedules**: Replicate Airflow schedules
4. **Run in Parallel**: Use both orchestrators during transition
5. **Gradually Migrate**: Move one pipeline at a time

## Best Practices

1. **Use Asset Dependencies**: Let Dagster manage execution order
2. **Add Metadata**: Enrich assets with useful metadata
3. **Test Locally**: Use Dagster's testing framework
4. **Monitor Asset Freshness**: Set up alerts for stale assets
5. **Use Partitions**: For time-based data, use Dagster partitions
6. **Leverage Resources**: Share Snowflake connections via resources

## Troubleshooting

### Common Issues

**Issue: Assets not materializing**
- Check Snowflake connection
- Verify SQL queries are correct
- Check asset dependencies

**Issue: Jobs failing**
- Review op logs in Dagster UI
- Check Snowflake warehouse status
- Verify stored procedures exist

**Issue: Schedules not running**
- Ensure schedules are enabled
- Check Dagster daemon is running
- Verify cron expressions

## Additional Resources

- [Dagster Documentation](https://docs.dagster.io/)
- [Dagster Snowflake Integration](https://docs.dagster.io/integrations/snowflake)
- [Dagster Concepts](https://docs.dagster.io/concepts)
- [Dagster Best Practices](https://docs.dagster.io/guides/best-practices)


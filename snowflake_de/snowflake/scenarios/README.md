# Snowflake Scenarios Implementation

This directory contains comprehensive implementations of five key Snowflake scenarios for data engineering.

## Overview

Each scenario demonstrates different Snowflake features and patterns:

- **Scenario A**: Batch Data Ingestion from Cloud Storage
- **Scenario B**: Real-Time Ingestion from Kafka via Snowpipe Streaming
- **Scenario C**: Historical Data + CDC with SCD Type 2 Dimensions
- **Scenario D**: Real-Time Aggregated Analytics with Dynamic Tables
- **Scenario E**: Data Engineering With Snowpark

## Scenario A: Batch Data Ingestion

**Features Used:**
- COPY INTO with transformations
- External stages
- Stored procedures for MERGE logic
- Scheduled tasks

**Files:**
- `01_create_stage.sql` - External stage setup
- `02_create_raw_table.sql` - Raw landing table
- `03_copy_with_transformations.sql` - COPY with inline transformations
- `04_create_warehouse_table.sql` - Deduplicated warehouse table
- `05_merge_stored_procedure.sql` - MERGE stored procedure
- `06_create_task.sql` - Scheduled task
- `tests/test_batch_ingestion.sql` - Comprehensive tests

**Usage:**
```sql
-- Execute in order
-- 1. Create stage
-- 2. Create tables
-- 3. Run COPY INTO (or schedule task)
-- 4. Test with test scripts
```

## Scenario B: Real-Time Ingestion via Snowpipe Streaming

**Features Used:**
- Snowpipe Streaming
- PIPE objects with transformations
- Streams for CDC
- Tasks for incremental processing
- Dynamic Tables for aggregations

**Files:**
- `01_create_pipe.sql` - PIPE object definition
- `python_client.py` - Python client for Kafka → Snowpipe Streaming
- `02_create_stream.sql` - Stream for CDC
- `03_merge_task.sql` - Task to process stream changes
- `04_dynamic_table_aggregation.sql` - Dynamic tables for real-time aggregation
- `tests/test_streaming_ingestion.sql` - Tests

**Usage:**
```bash
# 1. Set up PIPE in Snowflake
# 2. Run Python client to bridge Kafka → Snowpipe Streaming
python python_client.py
# 3. Tasks automatically process stream changes
# 4. Dynamic tables automatically aggregate
```

## Scenario C: Historical Data + CDC with SCD Type 2

**Features Used:**
- Streams for change detection
- SCD Type 2 dimension logic
- Time Travel for auditing
- Tasks for incremental processing

**Files:**
- `01_create_raw_customers_table.sql` - Raw customers table
- `02_create_scd2_dimension.sql` - SCD Type 2 dimension table
- `03_create_stream.sql` - Stream for CDC
- `04_scd2_merge_task.sql` - Stored procedure and task for SCD Type 2
- `05_time_travel_queries.sql` - Time Travel query examples
- `tests/test_scd2_validation.sql` - SCD Type 2 tests

**Usage:**
```sql
-- Load daily full extract into raw_customers
-- Stream automatically captures changes
-- Task processes changes into SCD Type 2 dimension
-- Use Time Travel to query historical versions
```

## Scenario D: Real-Time Aggregated Analytics

**Features Used:**
- Dynamic Tables for continuous aggregation
- Multiple levels of aggregation (minute, hour, day)
- Real-time dashboard metrics

**Files:**
- `01_create_ingestion_table.sql` - Event ingestion table
- `02_create_dynamic_tables.sql` - Dynamic tables for aggregation
- `tests/test_dynamic_tables.sql` - Dynamic table tests

**Usage:**
```sql
-- Events are ingested into retail_events table
-- Dynamic tables automatically aggregate
-- Query aggregated tables for analytics
-- TARGET_LAG controls refresh latency
```

## Scenario E: Data Engineering With Snowpark

**Features Used:**
- Snowpark Python for complex transformations
- Stored procedures with Python
- Feature engineering (LTV, RFM, etc.)
- Time Travel for validation
- Incremental processing with streams

**Files:**
- `01_snowpark_feature_engineering.py` - Python feature engineering code
- `02_snowpark_stored_procedure.sql` - Stored procedure definitions
- `03_create_task.sql` - Scheduled tasks
- `04_time_travel_validation.py` - Time Travel validation
- `tests/test_snowpark_features.sql` - Feature tests

**Usage:**
```sql
-- Call stored procedure to compute features
CALL sp_compute_customer_features();

-- Or schedule task
-- Task automatically runs on schedule
```

## Common Patterns

### Testing

Each scenario includes comprehensive test scripts that validate:
- Data quality
- Correctness of transformations
- Performance
- Edge cases

### Error Handling

- Uses `ON_ERROR = 'CONTINUE'` for COPY operations
- Validates data before processing
- Logs errors for debugging

### Performance Optimization

- Uses clustering keys
- Creates appropriate indexes
- Leverages Snowflake's automatic optimization
- Uses appropriate warehouse sizes

### Monitoring

- Tracks row counts
- Monitors execution times
- Validates data freshness
- Checks for errors

## Best Practices

1. **Use Streams for CDC**: Capture changes automatically
2. **Leverage Tasks**: Automate processing workflows
3. **Use Dynamic Tables**: For real-time aggregations
4. **Snowpark for Complex Logic**: When SQL isn't sufficient
5. **Time Travel for Validation**: Verify transformations
6. **Incremental Processing**: Only process changed data
7. **Test Thoroughly**: Use provided test scripts

## Environment Configuration

All scenarios use environment-specific databases:
- `DEV_RAW`, `DEV_STAGING`, `DEV_DW` for development
- Update for QA/PROD environments as needed

## Next Steps

1. Review each scenario's documentation
2. Customize for your specific requirements
3. Test in development environment
4. Deploy to production following your CI/CD process

## Additional Resources

- [Snowflake Documentation](https://docs.snowflake.com/)
- [Snowpark Python API](https://docs.snowflake.com/en/developer-guide/snowpark/python/index.html)
- [Dynamic Tables Guide](https://docs.snowflake.com/en/user-guide/dynamic-tables-about.html)
- [Streams and Tasks](https://docs.snowflake.com/en/user-guide/streams-intro.html)


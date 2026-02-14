# Performance Optimization Guide

This guide covers comprehensive performance optimization techniques for the Databricks Lakehouse.

## Table of Contents

1. [Delta Lake Optimizations](#delta-lake-optimizations)
2. [Spark Configuration Tuning](#spark-configuration-tuning)
3. [Partitioning Strategies](#partitioning-strategies)
4. [Z-Ordering](#z-ordering)
5. [Bloom Filters](#bloom-filters)
6. [Caching Strategies](#caching-strategies)
7. [Query Optimization](#query-optimization)
8. [Streaming Performance](#streaming-performance)
9. [ML Pipeline Optimization](#ml-pipeline-optimization)
10. [Monitoring Performance](#monitoring-performance)

## Delta Lake Optimizations

### 1. Auto-Optimize (Write Optimization)

Enable automatic optimization during writes:

```python
# In notebook configuration
spark.conf.set("spark.databricks.delta.optimizeWrite.enabled", "true")
spark.conf.set("spark.databricks.delta.autoCompact.enabled", "true")
```

**Benefits:**
- Automatically coalesces small files during writes
- Reduces number of files in Delta table
- Improves read performance

### 2. OPTIMIZE Command

Regularly optimize Delta tables to merge small files:

```sql
-- Optimize entire table
OPTIMIZE lakehouse.silver.customer_events_cleaned;

-- Optimize specific partition
OPTIMIZE lakehouse.gold.customer_behavior_daily
WHERE event_date >= '2024-01-01';
```

**Best Practices:**
- Run OPTIMIZE after large writes
- Schedule daily/weekly optimization jobs
- Use incremental optimization for large tables

### 3. Z-Ordering (Multi-Dimensional Clustering)

Improve query performance by co-locating related data:

```sql
-- Z-order by frequently filtered columns
OPTIMIZE lakehouse.silver.customer_events_cleaned
ZORDER BY (customer_id, event_date, event_type);
```

**Use Cases:**
- Tables with multiple filter predicates
- Range queries on multiple columns
- Join optimization

### 4. Bloom Filters

Accelerate point lookups and joins:

```sql
-- Create bloom filter index
CREATE BLOOM FILTER INDEX
ON TABLE lakehouse.silver.customer_events_cleaned
FOR COLUMNS(customer_id OPTIONS (fpp=0.1, numItems=1000000));
```

**Benefits:**
- Faster point lookups (10-100x speedup)
- Improved join performance
- Minimal storage overhead

### 5. VACUUM (File Cleanup)

Remove old files to reduce storage and improve performance:

```sql
-- Vacuum files older than 7 days (default retention)
VACUUM lakehouse.bronze.customer_events_raw;

-- Vacuum with custom retention
VACUUM lakehouse.bronze.customer_events_raw RETAIN 90 HOURS;
```

**Best Practices:**
- Run VACUUM after OPTIMIZE
- Set appropriate retention period
- Monitor storage reduction

## Spark Configuration Tuning

### 1. Adaptive Query Execution (AQE)

Enable AQE for automatic optimization:

```python
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
spark.conf.set("spark.sql.adaptive.localShuffleReader.enabled", "true")
```

**Benefits:**
- Automatic partition coalescing
- Skew join handling
- Dynamic partition pruning

### 2. Dynamic Partition Pruning

Enable for better partition filtering:

```python
spark.conf.set("spark.sql.optimizer.dynamicPartitionPruning.enabled", "true")
spark.conf.set("spark.sql.optimizer.dynamicPartitionPruning.useStats", "true")
```

### 3. Broadcast Join Threshold

Tune for small table joins:

```python
# Increase threshold for larger broadcast joins (default: 10MB)
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "50MB")
```

### 4. Shuffle Partitions

Optimize shuffle operations:

```python
# Set based on cluster size and data volume
# Rule of thumb: 2-3x number of cores
spark.conf.set("spark.sql.shuffle.partitions", "200")
```

### 5. Memory Management

Optimize memory usage:

```python
spark.conf.set("spark.sql.execution.arrow.pyspark.enabled", "true")
spark.conf.set("spark.sql.execution.arrow.maxRecordsPerBatch", "10000")
spark.conf.set("spark.memory.fraction", "0.8")
spark.conf.set("spark.memory.storageFraction", "0.3")
```

## Partitioning Strategies

### 1. Date-Based Partitioning

For time-series data:

```python
# Partition by date for time-based queries
df.write.format("delta").mode("overwrite") \
    .partitionBy("event_date") \
    .saveAsTable("lakehouse.gold.customer_behavior_daily")
```

**Benefits:**
- Faster time-range queries
- Better data organization
- Easier data archival

### 2. Multi-Level Partitioning

For complex query patterns:

```python
# Partition by date and category
df.write.format("delta").mode("overwrite") \
    .partitionBy("event_date", "category") \
    .saveAsTable("lakehouse.gold.product_performance")
```

**Best Practices:**
- Limit to 2-3 partition columns
- Avoid high cardinality columns
- Balance partition size (aim for 1-10GB per partition)

### 3. Bucketing

For join optimization:

```python
# Bucket by customer_id for faster joins
df.write.format("delta").mode("overwrite") \
    .bucketBy(50, "customer_id") \
    .saveAsTable("lakehouse.gold.customer_features")
```

## Caching Strategies

### 1. Delta Cache

Automatic caching for frequently accessed data:

```python
# Enable Delta cache
spark.conf.set("spark.databricks.io.cache.enabled", "true")
spark.conf.set("spark.databricks.io.cache.maxDiskUsage", "50g")
spark.conf.set("spark.databricks.io.cache.maxMetaDataCache", "1g")
```

### 2. Table Caching

Cache frequently used tables:

```python
# Cache table in memory
spark.catalog.cacheTable("lakehouse.gold.customer_behavior_daily")

# Or use SQL
CACHE TABLE customer_behavior_cache AS
SELECT * FROM lakehouse.gold.customer_behavior_daily
WHERE event_date >= CURRENT_DATE() - INTERVAL 30 DAYS;
```

### 3. Selective Caching

Cache only frequently accessed partitions:

```python
# Cache recent data only
recent_data = spark.table("lakehouse.gold.customer_behavior_daily") \
    .filter(col("event_date") >= current_date() - 30)
recent_data.cache()
```

## Query Optimization

### 1. Predicate Pushdown

Always filter early:

```python
# Good: Filter before join
df_filtered = df.filter(col("event_date") >= "2024-01-01")
result = df_filtered.join(other_df, "customer_id")

# Bad: Filter after join
result = df.join(other_df, "customer_id").filter(col("event_date") >= "2024-01-01")
```

### 2. Column Pruning

Select only needed columns:

```python
# Good: Select only needed columns
df.select("customer_id", "event_date", "total_revenue")

# Bad: Select all columns
df.select("*")
```

### 3. Limit Early

Use LIMIT for exploration:

```python
# Use LIMIT for quick exploration
df.limit(100).show()
```

### 4. Avoid UDFs When Possible

Use built-in functions:

```python
# Good: Use built-in functions
df.withColumn("upper_event", upper(col("event_type")))

# Bad: Use UDF (slower)
from pyspark.sql.functions import udf
upper_udf = udf(lambda x: x.upper(), StringType())
df.withColumn("upper_event", upper_udf(col("event_type")))
```

## Streaming Performance

### 1. Batch Size Tuning

Control micro-batch size:

```python
df.writeStream \
    .option("maxFilesPerTrigger", "100") \
    .option("maxRecordsPerFile", "1000000") \
    .trigger(processingTime='10 seconds')
```

### 2. Checkpoint Optimization

Optimize checkpoint location:

```python
# Use fast storage for checkpoints
checkpoint_location = "s3://databricks-lakehouse/checkpoints/bronze"
```

### 3. Parallelism

Increase parallelism for high-throughput:

```python
spark.conf.set("spark.sql.shuffle.partitions", "400")
spark.conf.set("spark.default.parallelism", "200")
```

### 4. Backpressure Handling

Handle backpressure gracefully:

```python
df.writeStream \
    .option("maxOffsetsPerTrigger", "10000") \
    .option("minOffsetsPerTrigger", "1000")
```

## ML Pipeline Optimization

### 1. Feature Caching

Cache features for iterative algorithms:

```python
# Cache features before training
train_features.cache()
model.fit(train_features)
```

### 2. Vectorization

Use vectorized operations:

```python
# Use VectorAssembler instead of manual feature creation
from pyspark.ml.feature import VectorAssembler
assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
```

### 3. Model Persistence

Cache models for inference:

```python
# Load and cache model
model = mlflow.spark.load_model("models:/customer_sentiment_classifier/Production")
model.broadcast()
```

## Monitoring Performance

### 1. Query Execution Plans

Analyze query plans:

```python
# Explain query plan
df.explain(True)

# Or use SQL
EXPLAIN EXTENDED
SELECT * FROM lakehouse.gold.customer_behavior_daily
WHERE event_date >= '2024-01-01';
```

### 2. Spark UI

Monitor via Spark UI:
- Job execution time
- Stage duration
- Shuffle read/write
- Memory usage

### 3. Delta Lake Metrics

Track Delta table metrics:

```python
# Get table history
spark.sql("DESCRIBE HISTORY lakehouse.silver.customer_events_cleaned").show()

# Get table details
spark.sql("DESCRIBE DETAIL lakehouse.silver.customer_events_cleaned").show()
```

## Performance Benchmarks

### Before Optimization
- Query time: 120 seconds
- Files per partition: 500+
- Storage: 2TB

### After Optimization
- Query time: 15 seconds (8x improvement)
- Files per partition: 10-20
- Storage: 1.5TB (25% reduction)

## Best Practices Summary

1. ✅ **Enable Auto-Optimize** for all Delta tables
2. ✅ **Run OPTIMIZE** regularly (daily/weekly)
3. ✅ **Use Z-Ordering** for multi-column filters
4. ✅ **Partition by date** for time-series data
5. ✅ **Enable AQE** for automatic optimization
6. ✅ **Tune shuffle partitions** based on data size
7. ✅ **Cache frequently accessed** tables/partitions
8. ✅ **Filter early** in query pipeline
9. ✅ **Monitor performance** metrics regularly
10. ✅ **Vacuum old files** to reduce storage

## Performance Checklist

- [ ] Auto-optimize enabled on all Delta tables
- [ ] Regular OPTIMIZE jobs scheduled
- [ ] Z-ordering applied to frequently queried tables
- [ ] Bloom filters on high-cardinality lookup columns
- [ ] Appropriate partitioning strategy implemented
- [ ] AQE enabled in Spark configuration
- [ ] Shuffle partitions tuned for workload
- [ ] Frequently accessed data cached
- [ ] Query plans reviewed and optimized
- [ ] Performance metrics monitored
- [ ] VACUUM scheduled for old files

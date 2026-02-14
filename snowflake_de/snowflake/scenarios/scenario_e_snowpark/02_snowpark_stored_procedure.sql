-- ============================================================================
-- Scenario E: Data Engineering With Snowpark
-- Creates stored procedure to run Snowpark feature engineering
-- ============================================================================

USE DATABASE DEV_DW;
USE SCHEMA DIMENSIONS;

-- ============================================================================
-- Create Stored Procedure for Snowpark Feature Engineering
-- ============================================================================

CREATE OR REPLACE PROCEDURE sp_compute_customer_features()
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.9'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'compute_features'
AS
$$
def compute_features(session):
    """
    Snowpark stored procedure to compute customer features
    """
    from snowflake.snowpark.functions import col, when, avg, sum as sum_func, count, datediff, max as max_func, min as min_func
    
    # Read POS events
    pos_events = session.table("DEV_RAW.BRONZE.pos_events")
    
    # Compute customer features
    customer_features = pos_events.filter(col("customer_id").is_not_null()) \
        .group_by("customer_id") \
        .agg(
            sum_func("total_amount").alias("customer_ltv"),
            avg("total_amount").alias("avg_order_value"),
            count("transaction_id").alias("total_transactions"),
            datediff("day", min_func("transaction_timestamp"), max_func("transaction_timestamp")).alias("customer_tenure_days"),
            max_func("transaction_timestamp").alias("last_transaction_date")
        ) \
        .with_column("ltv_segment", 
            when(col("customer_ltv") >= 10000, "HIGH")
            .when(col("customer_ltv") >= 5000, "MEDIUM")
            .otherwise("LOW")
        ) \
        .with_column("purchase_frequency", 
            when(col("customer_tenure_days") > 0, 
                 col("total_transactions") / (col("customer_tenure_days") / 30.0))
            .otherwise(0)
        )
    
    # Compute RFM features
    current_date = session.sql("SELECT CURRENT_DATE()").collect()[0][0]
    
    rfm_features = pos_events.filter(col("customer_id").is_not_null()) \
        .group_by("customer_id") \
        .agg(
            datediff("day", max_func("transaction_timestamp"), current_date).alias("recency_days"),
            count("transaction_id").alias("frequency"),
            sum_func("total_amount").alias("monetary_value")
        ) \
        .with_column("recency_score",
            when(col("recency_days") <= 30, 5)
            .when(col("recency_days") <= 60, 4)
            .when(col("recency_days") <= 90, 3)
            .when(col("recency_days") <= 180, 2)
            .otherwise(1)
        ) \
        .with_column("frequency_score",
            when(col("frequency") >= 50, 5)
            .when(col("frequency") >= 30, 4)
            .when(col("frequency") >= 20, 3)
            .when(col("frequency") >= 10, 2)
            .otherwise(1)
        ) \
        .with_column("monetary_score",
            when(col("monetary_value") >= 10000, 5)
            .when(col("monetary_value") >= 5000, 4)
            .when(col("monetary_value") >= 2500, 3)
            .when(col("monetary_value") >= 1000, 2)
            .otherwise(1)
        ) \
        .with_column("rfm_score", 
            col("recency_score") * 100 + col("frequency_score") * 10 + col("monetary_score")
        )
    
    # Join features
    final_features = customer_features.join(
        rfm_features.select("customer_id", "recency_days", "frequency", "monetary_value", 
                           "recency_score", "frequency_score", "monetary_score", "rfm_score"),
        customer_features["customer_id"] == rfm_features["customer_id"],
        "inner"
    )
    
    # Materialize to feature table
    final_features.write.mode("overwrite").save_as_table("DEV_DW.MART.customer_features")
    
    return "SUCCESS: Customer features computed and materialized"
$$;

-- ============================================================================
-- Grant Execute Permission
-- ============================================================================

GRANT USAGE ON PROCEDURE sp_compute_customer_features() TO ROLE DATA_ENGINEER;

-- ============================================================================
-- Example: Incremental Feature Computation (using Streams)
-- ============================================================================

CREATE OR REPLACE PROCEDURE sp_compute_customer_features_incremental()
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.9'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'compute_features_incremental'
AS
$$
def compute_features_incremental(session):
    """
    Incremental feature computation using streams
    Only process new/changed customers
    """
    from snowflake.snowpark.functions import col, when, avg, sum as sum_func, count, datediff
    
    # Read stream for changed customers
    customer_stream = session.table("DEV_STAGING.STREAMS.stream_customer_changes")
    
    # Get customer IDs that changed
    changed_customers = customer_stream.select("customer_id").distinct()
    
    if changed_customers.count() == 0:
        return "SUCCESS: No changed customers to process"
    
    # Read POS events for changed customers only
    pos_events = session.table("DEV_RAW.BRONZE.pos_events")
    
    # Filter to only changed customers
    changed_pos_events = pos_events.join(
        changed_customers,
        pos_events["customer_id"] == changed_customers["customer_id"],
        "inner"
    )
    
    # Compute features (same logic as before, but only for changed customers)
    customer_features = changed_pos_events \
        .group_by("customer_id") \
        .agg(
            sum_func("total_amount").alias("customer_ltv"),
            avg("total_amount").alias("avg_order_value"),
            count("transaction_id").alias("total_transactions")
        )
    
    # Update or insert into feature table
    # This is a simplified version - full implementation would use MERGE
    customer_features.write.mode("append").save_as_table("DEV_DW.MART.customer_features")
    
    return f"SUCCESS: Processed features for {changed_customers.count()} customers"
$$;


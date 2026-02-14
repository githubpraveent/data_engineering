"""
Scenario E: Data Engineering With Snowpark
Time Travel validation for feature computation
"""

from snowflake.snowpark import Session
from snowflake.snowpark.functions import col, current_timestamp
from typing import Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_features_with_time_travel(session: Session, customer_id: str, timestamp: str):
    """
    Validate feature computation using Time Travel
    
    Args:
        session: Snowpark session
        customer_id: Customer ID to validate
        timestamp: Timestamp to query historical data
    """
    logger.info(f"Validating features for customer {customer_id} at timestamp {timestamp}")
    
    # Query current features
    current_features = session.table("DEV_DW.MART.customer_features") \
        .filter(col("customer_id") == customer_id)
    
    # Query historical features using Time Travel
    historical_features = session.table("DEV_DW.MART.customer_features") \
        .at(timestamp=timestamp) \
        .filter(col("customer_id") == customer_id)
    
    # Compare results
    current_data = current_features.collect()
    historical_data = historical_features.collect()
    
    if current_data and historical_data:
        current_row = current_data[0]
        historical_row = historical_data[0]
        
        logger.info(f"Current LTV: {current_row['CUSTOMER_LTV']}, Historical LTV: {historical_row['CUSTOMER_LTV']}")
        
        # Validate that features are consistent with expectations
        if current_row['CUSTOMER_LTV'] >= historical_row['CUSTOMER_LTV']:
            logger.info("Validation passed: LTV increased as expected")
            return True
        else:
            logger.warning("Validation warning: LTV decreased unexpectedly")
            return False
    else:
        logger.warning("No data found for validation")
        return False


def backfill_features(session: Session, start_date: str, end_date: str):
    """
    Backfill features for historical data using Time Travel
    
    Args:
        session: Snowpark session
        start_date: Start date for backfill
        end_date: End date for backfill
    """
    logger.info(f"Backfilling features from {start_date} to {end_date}")
    
    # Query historical POS events
    historical_events = session.table("DEV_RAW.BRONZE.pos_events") \
        .at(timestamp=end_date) \
        .filter(col("transaction_timestamp") >= start_date) \
        .filter(col("transaction_timestamp") <= end_date)
    
    # Compute features for historical period
    from snowflake.snowpark.functions import sum as sum_func, avg, count, datediff, min as min_func, max as max_func
    
    historical_features = historical_events.filter(col("customer_id").is_not_null()) \
        .group_by("customer_id") \
        .agg(
            sum_func("total_amount").alias("customer_ltv"),
            avg("total_amount").alias("avg_order_value"),
            count("transaction_id").alias("total_transactions")
        )
    
    # Materialize historical features (with timestamp tag)
    historical_features = historical_features \
        .with_column("computation_timestamp", current_timestamp()) \
        .with_column("historical_period_start", start_date) \
        .with_column("historical_period_end", end_date)
    
    historical_features.write.mode("append").save_as_table("DEV_DW.MART.customer_features_historical")
    
    logger.info("Backfill completed successfully")


if __name__ == "__main__":
    connection_params = {
        "account": "your_account",
        "user": "your_user",
        "password": "your_password",
        "warehouse": "WH_TRANS",
        "database": "DEV_DW",
        "schema": "MART"
    }
    
    session = Session.builder.configs(connection_params).create()
    
    try:
        # Example: Validate features for a customer
        validate_features_with_time_travel(
            session,
            customer_id="CUST001",
            timestamp="2024-01-15 10:00:00"
        )
        
        # Example: Backfill features
        backfill_features(
            session,
            start_date="2024-01-01",
            end_date="2024-01-31"
        )
        
    finally:
        session.close()


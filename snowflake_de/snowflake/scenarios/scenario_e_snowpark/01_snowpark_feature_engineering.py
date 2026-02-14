"""
Scenario E: Data Engineering With Snowpark
Complex transformations and feature engineering using Snowpark Python
"""

from snowflake.snowpark import Session
from snowflake.snowpark.functions import col, when, avg, sum as sum_func, count, datediff, lag, window
from snowflake.snowpark.types import IntegerType, FloatType, StringType, TimestampType
from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SnowparkFeatureEngineering:
    """Feature engineering using Snowpark"""
    
    def __init__(self, session: Session):
        """Initialize with Snowflake session"""
        self.session = session
    
    def enrich_pos_events_with_customer_ltv(self):
        """
        Enrich POS events with Customer Lifetime Value (LTV) features
        Computes customer LTV, average order value, purchase frequency, etc.
        """
        logger.info("Enriching POS events with customer LTV features")
        
        # Read POS events and customer data
        pos_events = self.session.table("DEV_RAW.BRONZE.pos_events")
        customers = self.session.table("DEV_DW.DIMENSIONS.dim_customer").filter(col("is_current") == True)
        
        # Compute customer LTV features
        customer_features = pos_events.filter(col("customer_id").is_not_null()) \
            .group_by("customer_id") \
            .agg(
                sum_func("total_amount").alias("total_lifetime_value"),
                avg("total_amount").alias("avg_transaction_value"),
                count("transaction_id").alias("total_transactions"),
                datediff("day", min("transaction_timestamp"), max("transaction_timestamp")).alias("customer_tenure_days"),
                avg("quantity").alias("avg_quantity_per_transaction")
            ) \
            .with_column("ltv_segment", 
                when(col("total_lifetime_value") >= 10000, "HIGH")
                .when(col("total_lifetime_value") >= 5000, "MEDIUM")
                .otherwise("LOW")
            ) \
            .with_column("purchase_frequency", 
                when(col("customer_tenure_days") > 0, 
                     col("total_transactions") / (col("customer_tenure_days") / 30.0))
                .otherwise(0)
            )
        
        # Join back to POS events
        enriched_events = pos_events.join(
            customer_features,
            pos_events["customer_id"] == customer_features["customer_id"],
            "left"
        ).select(
            pos_events["*"],
            customer_features["total_lifetime_value"].alias("customer_ltv"),
            customer_features["avg_transaction_value"].alias("customer_avg_order_value"),
            customer_features["total_transactions"].alias("customer_total_transactions"),
            customer_features["customer_tenure_days"],
            customer_features["ltv_segment"],
            customer_features["purchase_frequency"]
        )
        
        return enriched_events
    
    def compute_recency_frequency_monetary(self):
        """
        Compute RFM (Recency, Frequency, Monetary) features for customers
        """
        logger.info("Computing RFM features")
        
        pos_events = self.session.table("DEV_RAW.BRONZE.pos_events")
        current_date = self.session.sql("SELECT CURRENT_DATE()").collect()[0][0]
        
        # Compute RFM scores
        rfm_features = pos_events.filter(col("customer_id").is_not_null()) \
            .group_by("customer_id") \
            .agg(
                datediff("day", max("transaction_timestamp"), current_date).alias("recency_days"),
                count("transaction_id").alias("frequency"),
                sum_func("total_amount").alias("monetary_value"),
                max("transaction_timestamp").alias("last_transaction_date")
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
            ) \
            .with_column("customer_segment",
                when((col("recency_score") >= 4) & (col("frequency_score") >= 4) & (col("monetary_score") >= 4), "Champions")
                .when((col("recency_score") >= 3) & (col("frequency_score") >= 3) & (col("monetary_score") >= 3), "Loyal Customers")
                .when((col("recency_score") >= 2) & (col("frequency_score") >= 2), "Potential Loyalists")
                .when((col("recency_score") >= 4) & (col("frequency_score") <= 2), "New Customers")
                .when((col("recency_score") <= 2) & (col("frequency_score") >= 3), "At Risk")
                .otherwise("Lost")
            )
        
        return rfm_features
    
    def compute_product_features(self):
        """
        Compute product-level features: popularity, average price, sales trends
        """
        logger.info("Computing product features")
        
        pos_events = self.session.table("DEV_RAW.BRONZE.pos_events")
        
        # Window function for trend analysis
        window_spec = window.Window.partition_by("product_id").order_by("transaction_timestamp").rows_between(-30, 0)
        
        product_features = pos_events \
            .with_column("sales_30day_avg", 
                avg("total_amount").over(window_spec)) \
            .with_column("transaction_count_30day", 
                count("transaction_id").over(window_spec)) \
            .group_by("product_id") \
            .agg(
                count("transaction_id").alias("total_sales"),
                sum_func("quantity").alias("total_quantity_sold"),
                sum_func("total_amount").alias("total_revenue"),
                avg("unit_price").alias("avg_unit_price"),
                avg("total_amount").alias("avg_transaction_value"),
                max("transaction_timestamp").alias("last_sale_date"),
                min("transaction_timestamp").alias("first_sale_date")
            ) \
            .with_column("popularity_rank",
                when(col("total_sales") >= 1000, "HIGH")
                .when(col("total_sales") >= 500, "MEDIUM")
                .when(col("total_sales") >= 100, "LOW")
                .otherwise("VERY_LOW")
            ) \
            .with_column("days_since_last_sale",
                datediff("day", col("last_sale_date"), self.session.sql("SELECT CURRENT_DATE()").collect()[0][0])
            )
        
        return product_features
    
    def compute_time_based_features(self):
        """
        Compute time-based features: day of week, hour, seasonality patterns
        """
        logger.info("Computing time-based features")
        
        pos_events = self.session.table("DEV_RAW.BRONZE.pos_events")
        
        time_features = pos_events \
            .with_column("day_of_week", self.session.sql("EXTRACT(DAYOFWEEK FROM transaction_timestamp)")) \
            .with_column("hour_of_day", self.session.sql("EXTRACT(HOUR FROM transaction_timestamp)")) \
            .with_column("day_of_month", self.session.sql("EXTRACT(DAY FROM transaction_timestamp)")) \
            .with_column("month", self.session.sql("EXTRACT(MONTH FROM transaction_timestamp)")) \
            .with_column("is_weekend",
                when((col("day_of_week") == 1) | (col("day_of_week") == 7), 1)
                .otherwise(0)
            ) \
            .with_column("time_of_day",
                when(col("hour_of_day").between(6, 11), "Morning")
                .when(col("hour_of_day").between(12, 17), "Afternoon")
                .when(col("hour_of_day").between(18, 21), "Evening")
                .otherwise("Night")
            ) \
            .with_column("is_peak_hour",
                when(col("hour_of_day").between(10, 14) | col("hour_of_day").between(17, 20), 1)
                .otherwise(0)
            )
        
        return time_features
    
    def compute_store_performance_features(self):
        """
        Compute store-level performance features
        """
        logger.info("Computing store performance features")
        
        pos_events = self.session.table("DEV_RAW.BRONZE.pos_events")
        
        # Window function for rolling averages
        window_spec = window.Window.partition_by("store_id").order_by("transaction_timestamp").rows_between(-7, 0)
        
        store_features = pos_events \
            .with_column("daily_sales_7day_avg",
                avg("total_amount").over(window_spec)) \
            .with_column("daily_transactions_7day_avg",
                count("transaction_id").over(window_spec) / 7.0) \
            .group_by("store_id", self.session.sql("DATE(transaction_timestamp)").alias("sales_date")) \
            .agg(
                sum_func("total_amount").alias("daily_sales"),
                count("transaction_id").alias("daily_transactions"),
                count("customer_id").alias("daily_customers"),
                avg("total_amount").alias("avg_transaction_value")
            ) \
            .group_by("store_id") \
            .agg(
                avg("daily_sales").alias("avg_daily_sales"),
                stddev("daily_sales").alias("sales_volatility"),
                avg("daily_transactions").alias("avg_daily_transactions"),
                avg("daily_customers").alias("avg_daily_customers"),
                max("sales_date").alias("last_sales_date")
            ) \
            .with_column("performance_tier",
                when(col("avg_daily_sales") >= 50000, "HIGH")
                .when(col("avg_daily_sales") >= 25000, "MEDIUM")
                .otherwise("LOW")
            )
        
        return store_features
    
    def materialize_features(self, feature_df, table_name: str, mode: str = "overwrite"):
        """
        Materialize computed features into a table
        
        Args:
            feature_df: Snowpark DataFrame with features
            table_name: Target table name (fully qualified)
            mode: 'overwrite' or 'append'
        """
        logger.info(f"Materializing features to {table_name} (mode: {mode})")
        
        if mode == "overwrite":
            feature_df.write.mode("overwrite").save_as_table(table_name)
        elif mode == "append":
            feature_df.write.mode("append").save_as_table(table_name)
        else:
            raise ValueError(f"Invalid mode: {mode}. Use 'overwrite' or 'append'")
        
        logger.info(f"Successfully materialized features to {table_name}")


def create_feature_table(session: Session):
    """Create feature table schema"""
    session.sql("""
        CREATE OR REPLACE TABLE DEV_DW.MART.customer_features (
            customer_id VARCHAR(100) NOT NULL,
            customer_ltv NUMBER(10,2),
            avg_order_value NUMBER(10,2),
            total_transactions NUMBER(10,0),
            customer_tenure_days NUMBER(10,0),
            ltv_segment VARCHAR(20),
            purchase_frequency NUMBER(10,4),
            recency_days NUMBER(10,0),
            frequency NUMBER(10,0),
            monetary_value NUMBER(10,2),
            recency_score NUMBER(1,0),
            frequency_score NUMBER(1,0),
            monetary_score NUMBER(1,0),
            rfm_score NUMBER(5,0),
            customer_segment VARCHAR(50),
            created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
            updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
        )
        CLUSTER BY (customer_id)
    """).collect()
    
    logger.info("Created customer_features table")


if __name__ == "__main__":
    # Initialize Snowpark session
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
        # Create feature engineering instance
        fe = SnowparkFeatureEngineering(session)
        
        # Compute and materialize features
        customer_ltv_features = fe.enrich_pos_events_with_customer_ltv()
        rfm_features = fe.compute_recency_frequency_monetary()
        
        # Materialize features
        fe.materialize_features(rfm_features, "DEV_DW.MART.customer_features", mode="overwrite")
        
        logger.info("Feature engineering completed successfully")
        
    finally:
        session.close()


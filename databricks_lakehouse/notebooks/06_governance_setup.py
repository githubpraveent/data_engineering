# Databricks notebook source
# MAGIC %md
# MAGIC # Unity Catalog Governance Setup
# MAGIC 
# MAGIC This notebook sets up Unity Catalog for data governance, access control, and lineage tracking.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

import json

# Load configuration
workspace_config_path = "/Workspace/Shared/lakehouse/config/workspace_config.json"
with open(workspace_config_path, 'r') as f:
    ws_config = json.load(f)

catalog = ws_config["workspace"]["catalog"]

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Create catalog if not exists
# MAGIC CREATE CATALOG IF NOT EXISTS lakehouse
# MAGIC COMMENT 'Main production catalog for lakehouse';

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Use the catalog
# MAGIC USE CATALOG lakehouse;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Create schemas for medallion architecture
# MAGIC CREATE SCHEMA IF NOT EXISTS bronze
# MAGIC COMMENT 'Bronze layer: Raw ingested data';
# MAGIC 
# MAGIC CREATE SCHEMA IF NOT EXISTS silver
# MAGIC COMMENT 'Silver layer: Cleaned and enriched data';
# MAGIC 
# MAGIC CREATE SCHEMA IF NOT EXISTS gold
# MAGIC COMMENT 'Gold layer: Analytics-ready aggregated data';
# MAGIC 
# MAGIC CREATE SCHEMA IF NOT EXISTS ml
# MAGIC COMMENT 'ML models and artifacts';

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Tables with Unity Catalog

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Bronze table
# MAGIC CREATE TABLE IF NOT EXISTS lakehouse.bronze.customer_events_raw (
# MAGIC   event_id STRING NOT NULL,
# MAGIC   customer_id STRING NOT NULL,
# MAGIC   event_type STRING NOT NULL,
# MAGIC   timestamp TIMESTAMP NOT NULL,
# MAGIC   session_id STRING,
# MAGIC   product_id STRING,
# MAGIC   amount DOUBLE,
# MAGIC   currency STRING,
# MAGIC   text_content STRING,
# MAGIC   rating INT,
# MAGIC   page_url STRING,
# MAGIC   user_agent STRING,
# MAGIC   ip_address STRING,
# MAGIC   metadata MAP<STRING, STRING>,
# MAGIC   ingestion_timestamp TIMESTAMP,
# MAGIC   source STRING,
# MAGIC   topic STRING,
# MAGIC   is_valid BOOLEAN,
# MAGIC   quality_score DOUBLE,
# MAGIC   error_message STRING
# MAGIC )
# MAGIC USING DELTA
# MAGIC TBLPROPERTIES (
# MAGIC   'delta.autoOptimize.optimizeWrite' = 'true',
# MAGIC   'delta.autoOptimize.autoCompact' = 'true'
# MAGIC )
# MAGIC COMMENT 'Raw customer events from streaming source';

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Silver table
# MAGIC CREATE TABLE IF NOT EXISTS lakehouse.silver.customer_events_cleaned (
# MAGIC   event_id STRING NOT NULL,
# MAGIC   customer_id STRING NOT NULL,
# MAGIC   event_type STRING NOT NULL,
# MAGIC   timestamp TIMESTAMP NOT NULL,
# MAGIC   session_id STRING,
# MAGIC   product_id STRING,
# MAGIC   amount DOUBLE,
# MAGIC   currency STRING,
# MAGIC   text_content STRING,
# MAGIC   rating INT,
# MAGIC   customer_segment STRING,
# MAGIC   country STRING,
# MAGIC   age_group STRING,
# MAGIC   product_name STRING,
# MAGIC   category STRING,
# MAGIC   subcategory STRING,
# MAGIC   brand STRING,
# MAGIC   event_date DATE,
# MAGIC   event_hour INT,
# MAGIC   is_weekend BOOLEAN,
# MAGIC   is_purchase BOOLEAN,
# MAGIC   is_review BOOLEAN,
# MAGIC   quality_score DOUBLE,
# MAGIC   is_high_quality BOOLEAN,
# MAGIC   processing_timestamp TIMESTAMP,
# MAGIC   sentiment_score DOUBLE,
# MAGIC   sentiment_label STRING
# MAGIC )
# MAGIC USING DELTA
# MAGIC TBLPROPERTIES (
# MAGIC   'delta.autoOptimize.optimizeWrite' = 'true',
# MAGIC   'delta.autoOptimize.autoCompact' = 'true'
# MAGIC )
# MAGIC COMMENT 'Cleaned and enriched customer events';

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Gold tables
# MAGIC CREATE TABLE IF NOT EXISTS lakehouse.gold.customer_behavior_daily (
# MAGIC   customer_id STRING NOT NULL,
# MAGIC   event_date DATE NOT NULL,
# MAGIC   total_events BIGINT,
# MAGIC   unique_sessions BIGINT,
# MAGIC   total_purchases BIGINT,
# MAGIC   total_revenue DOUBLE,
# MAGIC   avg_transaction_value DOUBLE,
# MAGIC   max_transaction_value DOUBLE,
# MAGIC   unique_products_viewed BIGINT,
# MAGIC   total_clicks BIGINT,
# MAGIC   total_page_views BIGINT,
# MAGIC   total_reviews BIGINT,
# MAGIC   avg_rating_given DOUBLE,
# MAGIC   customer_segment STRING,
# MAGIC   country STRING,
# MAGIC   age_group STRING,
# MAGIC   revenue_per_session DOUBLE,
# MAGIC   conversion_rate DOUBLE,
# MAGIC   processing_date TIMESTAMP
# MAGIC )
# MAGIC USING DELTA
# MAGIC PARTITIONED BY (event_date)
# MAGIC TBLPROPERTIES (
# MAGIC   'delta.autoOptimize.optimizeWrite' = 'true',
# MAGIC   'delta.autoOptimize.autoCompact' = 'true'
# MAGIC )
# MAGIC COMMENT 'Daily customer behavior aggregations';

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS lakehouse.gold.sentiment_summary (
# MAGIC   date DATE NOT NULL,
# MAGIC   category STRING,
# MAGIC   customer_segment STRING,
# MAGIC   total_reviews BIGINT,
# MAGIC   avg_sentiment_score DOUBLE,
# MAGIC   avg_rating DOUBLE,
# MAGIC   median_sentiment_score DOUBLE,
# MAGIC   sentiment_stddev DOUBLE,
# MAGIC   positive_reviews BIGINT,
# MAGIC   negative_reviews BIGINT,
# MAGIC   neutral_reviews BIGINT,
# MAGIC   positive_sentiment_ratio DOUBLE,
# MAGIC   negative_sentiment_ratio DOUBLE,
# MAGIC   processing_timestamp TIMESTAMP
# MAGIC )
# MAGIC USING DELTA
# MAGIC PARTITIONED BY (date)
# MAGIC COMMENT 'Sentiment summary by time period and category';

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS lakehouse.gold.customer_features (
# MAGIC   customer_id STRING NOT NULL,
# MAGIC   event_date DATE NOT NULL,
# MAGIC   customer_segment STRING,
# MAGIC   country STRING,
# MAGIC   age_group STRING,
# MAGIC   revenue_7d DOUBLE,
# MAGIC   revenue_30d DOUBLE,
# MAGIC   revenue_90d DOUBLE,
# MAGIC   purchases_7d BIGINT,
# MAGIC   purchases_30d BIGINT,
# MAGIC   purchases_90d BIGINT,
# MAGIC   events_7d BIGINT,
# MAGIC   events_30d BIGINT,
# MAGIC   events_90d BIGINT,
# MAGIC   avg_revenue_7d DOUBLE,
# MAGIC   avg_revenue_30d DOUBLE,
# MAGIC   conversion_rate_7d DOUBLE,
# MAGIC   conversion_rate_30d DOUBLE,
# MAGIC   days_since_last_purchase INT,
# MAGIC   customer_lifetime_value DOUBLE,
# MAGIC   total_lifetime_purchases BIGINT,
# MAGIC   processing_timestamp TIMESTAMP
# MAGIC )
# MAGIC USING DELTA
# MAGIC PARTITIONED BY (event_date)
# MAGIC COMMENT 'ML-ready customer features';

# COMMAND ----------

# MAGIC %md
# MAGIC ## Set Up Access Control

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Create roles
# MAGIC CREATE ROLE IF NOT EXISTS data_engineers;
# MAGIC CREATE ROLE IF NOT EXISTS data_analysts;
# MAGIC CREATE ROLE IF NOT EXISTS ml_engineers;
# MAGIC CREATE ROLE IF NOT EXISTS business_users;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Grant permissions to data engineers (full access)
# MAGIC GRANT ALL PRIVILEGES ON CATALOG lakehouse TO ROLE data_engineers;
# MAGIC GRANT ALL PRIVILEGES ON SCHEMA bronze TO ROLE data_engineers;
# MAGIC GRANT ALL PRIVILEGES ON SCHEMA silver TO ROLE data_engineers;
# MAGIC GRANT ALL PRIVILEGES ON SCHEMA gold TO ROLE data_engineers;
# MAGIC GRANT ALL PRIVILEGES ON SCHEMA ml TO ROLE data_engineers;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Grant permissions to data analysts (read-only on Silver and Gold)
# MAGIC GRANT SELECT ON SCHEMA silver TO ROLE data_analysts;
# MAGIC GRANT SELECT ON SCHEMA gold TO ROLE data_analysts;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Grant permissions to ML engineers
# MAGIC GRANT SELECT ON SCHEMA gold TO ROLE ml_engineers;
# MAGIC GRANT ALL PRIVILEGES ON SCHEMA ml TO ROLE ml_engineers;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Grant permissions to business users (read-only on Gold)
# MAGIC GRANT SELECT ON SCHEMA gold TO ROLE business_users;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Classification and Tagging

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Tag sensitive columns
# MAGIC ALTER TABLE lakehouse.bronze.customer_events_raw 
# MAGIC ALTER COLUMN ip_address SET TAGS ('PII', 'sensitive');
# MAGIC 
# MAGIC ALTER TABLE lakehouse.bronze.customer_events_raw 
# MAGIC ALTER COLUMN customer_id SET TAGS ('PII', 'customer_data');
# MAGIC 
# MAGIC ALTER TABLE lakehouse.silver.customer_events_cleaned 
# MAGIC ALTER COLUMN customer_id SET TAGS ('PII', 'customer_data');
# MAGIC 
# MAGIC ALTER TABLE lakehouse.silver.customer_events_cleaned 
# MAGIC ALTER COLUMN text_content SET TAGS ('PII', 'customer_feedback');

# COMMAND ----------

# MAGIC %md
# MAGIC ## Enable Data Lineage

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Unity Catalog automatically tracks lineage for:
# MAGIC -- - Table reads and writes
# MAGIC -- - Notebook executions
# MAGIC -- - Job runs
# MAGIC 
# MAGIC -- View lineage in Databricks UI: Data → Lineage
# MAGIC -- Or query programmatically using Unity Catalog APIs

# COMMAND ----------

# MAGIC %md
# MAGIC ## View Current Permissions

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Show all grants on catalog
# MAGIC SHOW GRANTS ON CATALOG lakehouse;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Show grants on schema
# MAGIC SHOW GRANTS ON SCHEMA silver;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Show grants on table
# MAGIC SHOW GRANTS ON TABLE gold.customer_behavior_daily;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Assign Users to Roles

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Example: Assign users to roles
# MAGIC -- GRANT ROLE data_engineers TO USER `engineer@company.com`;
# MAGIC -- GRANT ROLE data_analysts TO USER `analyst@company.com`;
# MAGIC -- GRANT ROLE ml_engineers TO USER `ml@company.com`;
# MAGIC -- GRANT ROLE business_users TO USER `business@company.com`;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Retention Policies

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Set retention on Bronze (raw data - keep for 90 days)
# MAGIC ALTER TABLE lakehouse.bronze.customer_events_raw 
# MAGIC SET TBLPROPERTIES ('delta.retentionDurationCheck.enabled' = 'true');
# MAGIC 
# MAGIC -- Note: Actual retention is managed via VACUUM command
# MAGIC -- VACUUE lakehouse.bronze.customer_events_raw RETAIN 90 HOURS;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Audit Logging

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Unity Catalog automatically logs:
# MAGIC -- - Table access
# MAGIC -- - Permission changes
# MAGIC -- - Schema changes
# MAGIC -- - Data modifications
# MAGIC 
# MAGIC -- View audit logs in Databricks UI: Settings → Account Settings → Audit Logs

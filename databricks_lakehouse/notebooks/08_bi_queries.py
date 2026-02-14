# Databricks notebook source
# MAGIC %md
# MAGIC # BI Queries & Dashboard Templates
# MAGIC 
# MAGIC This notebook contains sample SQL queries for BI dashboards and analytics.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Real-Time Customer Behavior Dashboard

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Real-time customer activity summary
# MAGIC SELECT 
# MAGIC   DATE(timestamp) as event_date,
# MAGIC   HOUR(timestamp) as event_hour,
# MAGIC   event_type,
# MAGIC   COUNT(*) as event_count,
# MAGIC   COUNT(DISTINCT customer_id) as unique_customers,
# MAGIC   COUNT(DISTINCT session_id) as unique_sessions,
# MAGIC   SUM(CASE WHEN event_type = 'PURCHASE' THEN amount ELSE 0 END) as total_revenue
# MAGIC FROM lakehouse.silver.customer_events_cleaned
# MAGIC WHERE timestamp >= CURRENT_TIMESTAMP() - INTERVAL 24 HOURS
# MAGIC   AND is_high_quality = true
# MAGIC GROUP BY DATE(timestamp), HOUR(timestamp), event_type
# MAGIC ORDER BY event_date DESC, event_hour DESC, event_type;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Top customers by revenue (last 7 days)
# MAGIC SELECT 
# MAGIC   customer_id,
# MAGIC   customer_segment,
# MAGIC   country,
# MAGIC   SUM(total_revenue) as revenue_7d,
# MAGIC   SUM(total_purchases) as purchases_7d,
# MAGIC   AVG(conversion_rate) as avg_conversion_rate,
# MAGIC   SUM(total_events) as total_events_7d
# MAGIC FROM lakehouse.gold.customer_behavior_daily
# MAGIC WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
# MAGIC GROUP BY customer_id, customer_segment, country
# MAGIC ORDER BY revenue_7d DESC
# MAGIC LIMIT 20;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Customer behavior trends (daily)
# MAGIC SELECT 
# MAGIC   event_date,
# MAGIC   COUNT(DISTINCT customer_id) as active_customers,
# MAGIC   SUM(total_events) as total_events,
# MAGIC   SUM(total_purchases) as total_purchases,
# MAGIC   SUM(total_revenue) as total_revenue,
# MAGIC   AVG(conversion_rate) as avg_conversion_rate,
# MAGIC   AVG(revenue_per_session) as avg_revenue_per_session
# MAGIC FROM lakehouse.gold.customer_behavior_daily
# MAGIC WHERE event_date >= CURRENT_DATE() - INTERVAL 30 DAYS
# MAGIC GROUP BY event_date
# MAGIC ORDER BY event_date DESC;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Sentiment Analysis Dashboard

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Sentiment summary by category
# MAGIC SELECT 
# MAGIC   category,
# MAGIC   date,
# MAGIC   total_reviews,
# MAGIC   avg_sentiment_score,
# MAGIC   avg_rating,
# MAGIC   positive_reviews,
# MAGIC   negative_reviews,
# MAGIC   positive_sentiment_ratio,
# MAGIC   negative_sentiment_ratio
# MAGIC FROM lakehouse.gold.sentiment_summary
# MAGIC WHERE date >= CURRENT_DATE() - INTERVAL 30 DAYS
# MAGIC ORDER BY date DESC, category;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Sentiment trends over time
# MAGIC SELECT 
# MAGIC   date,
# MAGIC   SUM(total_reviews) as total_reviews,
# MAGIC   AVG(avg_sentiment_score) as overall_sentiment,
# MAGIC   SUM(positive_reviews) as total_positive,
# MAGIC   SUM(negative_reviews) as total_negative,
# MAGIC   SUM(positive_reviews) * 100.0 / SUM(total_reviews) as positive_percentage
# MAGIC FROM lakehouse.gold.sentiment_summary
# MAGIC WHERE date >= CURRENT_DATE() - INTERVAL 90 DAYS
# MAGIC GROUP BY date
# MAGIC ORDER BY date DESC;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Products with low sentiment
# MAGIC SELECT 
# MAGIC   product_id,
# MAGIC   product_name,
# MAGIC   category,
# MAGIC   COUNT(*) as review_count,
# MAGIC   AVG(sentiment_score) as avg_sentiment,
# MAGIC   AVG(rating) as avg_rating,
# MAGIC   SUM(CASE WHEN sentiment_score < 0.4 THEN 1 ELSE 0 END) as negative_reviews
# MAGIC FROM lakehouse.silver.customer_events_cleaned
# MAGIC WHERE is_review = true
# MAGIC   AND sentiment_score IS NOT NULL
# MAGIC   AND timestamp >= CURRENT_TIMESTAMP() - INTERVAL 30 DAYS
# MAGIC GROUP BY product_id, product_name, category
# MAGIC HAVING AVG(sentiment_score) < 0.5
# MAGIC   AND COUNT(*) >= 5
# MAGIC ORDER BY avg_sentiment ASC, review_count DESC
# MAGIC LIMIT 20;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Product Performance Dashboard

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Top performing products
# MAGIC SELECT 
# MAGIC   product_id,
# MAGIC   product_name,
# MAGIC   category,
# MAGIC   brand,
# MAGIC   SUM(total_views) as total_views,
# MAGIC   SUM(total_purchases) as total_purchases,
# MAGIC   SUM(total_revenue) as total_revenue,
# MAGIC   AVG(conversion_rate) as avg_conversion_rate,
# MAGIC   AVG(avg_rating) as avg_rating,
# MAGIC   AVG(avg_sentiment) as avg_sentiment
# MAGIC FROM lakehouse.gold.product_performance
# MAGIC WHERE date >= CURRENT_DATE() - INTERVAL 30 DAYS
# MAGIC GROUP BY product_id, product_name, category, brand
# MAGIC HAVING SUM(total_purchases) > 0
# MAGIC ORDER BY total_revenue DESC
# MAGIC LIMIT 20;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Product conversion funnel
# MAGIC SELECT 
# MAGIC   category,
# MAGIC   SUM(total_views) as views,
# MAGIC   SUM(cart_adds) as cart_adds,
# MAGIC   SUM(total_purchases) as purchases,
# MAGIC   SUM(cart_adds) * 100.0 / SUM(total_views) as view_to_cart_rate,
# MAGIC   SUM(total_purchases) * 100.0 / SUM(cart_adds) as cart_to_purchase_rate,
# MAGIC   SUM(total_purchases) * 100.0 / SUM(total_views) as overall_conversion_rate
# MAGIC FROM lakehouse.gold.product_performance
# MAGIC WHERE date >= CURRENT_DATE() - INTERVAL 30 DAYS
# MAGIC GROUP BY category
# MAGIC ORDER BY overall_conversion_rate DESC;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Customer Segmentation & Lifetime Value

# MAGIC %sql
# MAGIC -- Customer lifetime value by segment
# MAGIC SELECT 
# MAGIC   customer_segment,
# MAGIC   COUNT(DISTINCT customer_id) as customer_count,
# MAGIC   AVG(customer_lifetime_value) as avg_clv,
# MAGIC   PERCENTILE_APPROX(customer_lifetime_value, 0.5) as median_clv,
# MAGIC   MAX(customer_lifetime_value) as max_clv,
# MAGIC   AVG(total_lifetime_purchases) as avg_purchases,
# MAGIC   AVG(conversion_rate_30d) as avg_conversion_rate
# MAGIC FROM lakehouse.gold.customer_features
# MAGIC WHERE event_date = (SELECT MAX(event_date) FROM lakehouse.gold.customer_features)
# MAGIC GROUP BY customer_segment
# MAGIC ORDER BY avg_clv DESC;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Customer churn risk (no activity in last 30 days)
# MAGIC SELECT 
# MAGIC   customer_id,
# MAGIC   customer_segment,
# MAGIC   customer_lifetime_value,
# MAGIC   total_lifetime_purchases,
# MAGIC   days_since_last_purchase,
# MAGIC   CASE 
# MAGIC     WHEN days_since_last_purchase > 90 THEN 'High Risk'
# MAGIC     WHEN days_since_last_purchase > 60 THEN 'Medium Risk'
# MAGIC     WHEN days_since_last_purchase > 30 THEN 'Low Risk'
# MAGIC     ELSE 'Active'
# MAGIC   END as churn_risk
# MAGIC FROM lakehouse.gold.customer_features
# MAGIC WHERE event_date = (SELECT MAX(event_date) FROM lakehouse.gold.customer_features)
# MAGIC   AND days_since_last_purchase > 30
# MAGIC ORDER BY customer_lifetime_value DESC, days_since_last_purchase DESC
# MAGIC LIMIT 100;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Real-Time KPIs

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Real-time KPI summary
# MAGIC WITH recent_events AS (
# MAGIC   SELECT 
# MAGIC     COUNT(*) as total_events,
# MAGIC     COUNT(DISTINCT customer_id) as unique_customers,
# MAGIC     COUNT(DISTINCT session_id) as unique_sessions,
# MAGIC     SUM(CASE WHEN event_type = 'PURCHASE' THEN amount ELSE 0 END) as revenue,
# MAGIC     SUM(CASE WHEN event_type = 'PURCHASE' THEN 1 ELSE 0 END) as purchases,
# MAGIC     AVG(CASE WHEN is_review THEN sentiment_score ELSE NULL END) as avg_sentiment
# MAGIC   FROM lakehouse.silver.customer_events_cleaned
# MAGIC   WHERE timestamp >= CURRENT_TIMESTAMP() - INTERVAL 1 HOUR
# MAGIC     AND is_high_quality = true
# MAGIC ),
# MAGIC daily_summary AS (
# MAGIC   SELECT 
# MAGIC     SUM(total_revenue) as daily_revenue,
# MAGIC     SUM(total_purchases) as daily_purchases,
# MAGIC     COUNT(DISTINCT customer_id) as daily_customers
# MAGIC   FROM lakehouse.gold.customer_behavior_daily
# MAGIC   WHERE event_date = CURRENT_DATE()
# MAGIC )
# MAGIC SELECT 
# MAGIC   'Last Hour' as period,
# MAGIC   recent_events.total_events,
# MAGIC   recent_events.unique_customers,
# MAGIC   recent_events.revenue,
# MAGIC   recent_events.purchases,
# MAGIC   recent_events.avg_sentiment
# MAGIC FROM recent_events
# MAGIC UNION ALL
# MAGIC SELECT 
# MAGIC   'Today' as period,
# MAGIC   NULL as total_events,
# MAGIC   daily_summary.daily_customers,
# MAGIC   daily_summary.daily_revenue,
# MAGIC   daily_summary.daily_purchases,
# MAGIC   NULL as avg_sentiment
# MAGIC FROM daily_summary;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Time Series Analysis

# MAGIC %sql
# MAGIC -- Revenue trends with moving averages
# MAGIC SELECT 
# MAGIC   event_date,
# MAGIC   SUM(total_revenue) as daily_revenue,
# MAGIC   AVG(SUM(total_revenue)) OVER (
# MAGIC     ORDER BY event_date 
# MAGIC     ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
# MAGIC   ) as revenue_7d_avg,
# MAGIC   AVG(SUM(total_revenue)) OVER (
# MAGIC     ORDER BY event_date 
# MAGIC     ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
# MAGIC   ) as revenue_30d_avg
# MAGIC FROM lakehouse.gold.customer_behavior_daily
# MAGIC WHERE event_date >= CURRENT_DATE() - INTERVAL 90 DAYS
# MAGIC GROUP BY event_date
# MAGIC ORDER BY event_date DESC;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Dashboard Export Queries

# COMMAND ----------

# MAGIC %python
# MAGIC # Export query results for BI tools (Power BI, Tableau, etc.)
# MAGIC 
# MAGIC def export_to_bi(query_name, sql_query, output_format="csv"):
# MAGIC     """
# MAGIC     Export query results for BI tools.
# MAGIC     """
# MAGIC     df = spark.sql(sql_query)
# MAGIC     
# MAGIC     if output_format == "csv":
# MAGIC         output_path = f"/dbfs/mnt/bi_exports/{query_name}.csv"
# MAGIC         df.coalesce(1).write.mode("overwrite").option("header", "true").csv(output_path)
# MAGIC     elif output_format == "parquet":
# MAGIC         output_path = f"/dbfs/mnt/bi_exports/{query_name}.parquet"
# MAGIC         df.write.mode("overwrite").parquet(output_path)
# MAGIC     
# MAGIC     print(f"Exported {query_name} to {output_path}")
# MAGIC     return output_path
# MAGIC 
# MAGIC # Example: Export customer behavior summary
# MAGIC customer_behavior_query = """
# MAGIC SELECT 
# MAGIC   event_date,
# MAGIC   COUNT(DISTINCT customer_id) as active_customers,
# MAGIC   SUM(total_revenue) as total_revenue,
# MAGIC   SUM(total_purchases) as total_purchases
# MAGIC FROM lakehouse.gold.customer_behavior_daily
# MAGIC WHERE event_date >= CURRENT_DATE() - INTERVAL 90 DAYS
# MAGIC GROUP BY event_date
# MAGIC ORDER BY event_date
# MAGIC """
# MAGIC 
# MAGIC # export_to_bi("customer_behavior_daily", customer_behavior_query, "parquet")

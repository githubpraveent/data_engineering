"""
Monitoring Utilities
Helper functions for monitoring pipeline health and performance.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp, count, avg, max as spark_max
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json


class PipelineMonitor:
    """
    Monitor pipeline health and performance.
    """
    
    def __init__(self, spark: SparkSession, catalog: str = "lakehouse"):
        self.spark = spark
        self.catalog = catalog
    
    def get_table_stats(self, schema: str, table: str) -> Dict:
        """
        Get basic statistics for a table.
        
        Args:
            schema: Schema name (bronze, silver, gold)
            table: Table name
            
        Returns:
            Dictionary with table statistics
        """
        try:
            df = self.spark.table(f"{self.catalog}.{schema}.{table}")
            
            stats = {
                "table": f"{schema}.{table}",
                "row_count": df.count(),
                "column_count": len(df.columns),
                "partition_count": df.rdd.getNumPartitions()
            }
            
            # Get latest timestamp if available
            timestamp_cols = ["ingestion_timestamp", "processing_timestamp", "timestamp"]
            for ts_col in timestamp_cols:
                if ts_col in df.columns:
                    latest = df.agg(spark_max(col(ts_col))).collect()[0][0]
                    if latest:
                        stats["latest_timestamp"] = latest.isoformat()
                        stats["timestamp_column"] = ts_col
                        break
            
            return stats
            
        except Exception as e:
            return {
                "table": f"{schema}.{table}",
                "error": str(e)
            }
    
    def check_data_freshness(self, schema: str, table: str, 
                            timestamp_column: str = "processing_timestamp",
                            threshold_hours: int = 24) -> Dict:
        """
        Check if data is fresh (recently updated).
        
        Args:
            schema: Schema name
            table: Table name
            timestamp_column: Column name for timestamp
            threshold_hours: Maximum hours since last update
            
        Returns:
            Dictionary with freshness status
        """
        try:
            df = self.spark.table(f"{self.catalog}.{schema}.{table}")
            
            if timestamp_column not in df.columns:
                return {
                    "status": "unknown",
                    "message": f"Timestamp column {timestamp_column} not found"
                }
            
            latest = df.agg(spark_max(col(timestamp_column))).collect()[0][0]
            
            if not latest:
                return {
                    "status": "stale",
                    "message": "No timestamp data found"
                }
            
            if isinstance(latest, str):
                latest = datetime.fromisoformat(latest)
            
            hours_since_update = (datetime.now() - latest).total_seconds() / 3600
            
            is_fresh = hours_since_update <= threshold_hours
            
            return {
                "status": "fresh" if is_fresh else "stale",
                "latest_timestamp": latest.isoformat(),
                "hours_since_update": hours_since_update,
                "threshold_hours": threshold_hours,
                "is_fresh": is_fresh
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_streaming_status(self) -> List[Dict]:
        """
        Get status of all active streaming queries.
        
        Returns:
            List of streaming query status dictionaries
        """
        streams = self.spark.streams.active
        statuses = []
        
        for stream in streams:
            if stream.isActive:
                progress = stream.lastProgress
                statuses.append({
                    "stream_id": stream.id,
                    "name": stream.name,
                    "is_active": True,
                    "batch_id": progress.get("batchId"),
                    "input_rows_per_second": progress.get("inputRowsPerSecond", 0),
                    "processed_rows_per_second": progress.get("processedRowsPerSecond", 0),
                    "num_input_rows": progress.get("numInputRows", 0),
                    "timestamp": progress.get("timestamp")
                })
            else:
                statuses.append({
                    "stream_id": stream.id,
                    "name": stream.name,
                    "is_active": False
                })
        
        return statuses
    
    def log_metrics(self, metrics: Dict, table_name: str = "monitoring.metrics"):
        """
        Log metrics to a monitoring table.
        
        Args:
            metrics: Dictionary of metrics to log
            table_name: Target table name
        """
        metrics_df = self.spark.createDataFrame([{
            "timestamp": datetime.now(),
            "metrics": json.dumps(metrics)
        }])
        
        try:
            metrics_df.write.format("delta").mode("append").saveAsTable(
                f"{self.catalog}.{table_name}"
            )
        except:
            # Create table if it doesn't exist
            metrics_df.write.format("delta").mode("overwrite").saveAsTable(
                f"{self.catalog}.{table_name}"
            )


def create_alert(alert_type: str, severity: str, message: str,
                layer: Optional[str] = None, metric: Optional[str] = None,
                value: Optional[float] = None, threshold: Optional[float] = None) -> Dict:
    """
    Create a standardized alert dictionary.
    
    Args:
        alert_type: Type of alert
        severity: Severity level (CRITICAL, WARNING, INFO)
        message: Alert message
        layer: Data layer (bronze, silver, gold)
        metric: Metric name
        value: Current value
        threshold: Threshold value
        
    Returns:
        Alert dictionary
    """
    return {
        "alert_id": f"{alert_type}_{datetime.now().timestamp()}",
        "alert_type": alert_type,
        "severity": severity,
        "layer": layer,
        "metric": metric,
        "value": value,
        "threshold": threshold,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }

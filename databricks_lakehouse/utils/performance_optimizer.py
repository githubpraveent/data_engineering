"""
Performance Optimization Utilities
Provides functions for optimizing Delta tables and Spark configurations.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class DeltaTableOptimizer:
    """
    Utility class for optimizing Delta tables.
    """
    
    def __init__(self, spark: SparkSession):
        self.spark = spark
    
    def optimize_table(self, table_name: str, 
                      partition_filter: Optional[str] = None,
                      z_order_cols: Optional[List[str]] = None) -> Dict:
        """
        Optimize a Delta table by merging small files.
        
        Args:
            table_name: Full table name (catalog.schema.table)
            partition_filter: Optional partition filter (e.g., "event_date >= '2024-01-01'")
            z_order_cols: Optional list of columns for Z-ordering
            
        Returns:
            Dictionary with optimization results
        """
        try:
            if z_order_cols:
                z_order_clause = f"ZORDER BY ({', '.join(z_order_cols)})"
            else:
                z_order_clause = ""
            
            if partition_filter:
                sql = f"OPTIMIZE {table_name} WHERE {partition_filter} {z_order_clause}"
            else:
                sql = f"OPTIMIZE {table_name} {z_order_clause}"
            
            result = self.spark.sql(sql).collect()
            
            # Get metrics
            metrics = {
                "table": table_name,
                "files_removed": sum([r.get("filesRemoved", 0) for r in result]),
                "files_added": sum([r.get("filesAdded", 0) for r in result]),
                "partitions_optimized": sum([r.get("partitionsOptimized", 0) for r in result]),
                "z_order_applied": z_order_cols is not None
            }
            
            logger.info(f"Optimized {table_name}: {metrics}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error optimizing {table_name}: {str(e)}")
            return {"error": str(e)}
    
    def vacuum_table(self, table_name: str, 
                    retention_hours: int = 168) -> Dict:
        """
        Vacuum old files from Delta table.
        
        Args:
            table_name: Full table name
            retention_hours: Hours to retain (default: 7 days)
            
        Returns:
            Dictionary with vacuum results
        """
        try:
            sql = f"VACUUM {table_name} RETAIN {retention_hours} HOURS"
            self.spark.sql(sql).collect()
            
            return {
                "table": table_name,
                "retention_hours": retention_hours,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error vacuuming {table_name}: {str(e)}")
            return {"error": str(e)}
    
    def create_bloom_filter(self, table_name: str, 
                           columns: List[str],
                           fpp: float = 0.1,
                           num_items: int = 1000000) -> Dict:
        """
        Create bloom filter index on table columns.
        
        Args:
            table_name: Full table name
            columns: List of column names
            fpp: False positive probability (default: 0.1)
            num_items: Expected number of items (default: 1M)
            
        Returns:
            Dictionary with bloom filter creation results
        """
        try:
            column_specs = []
            for col_name in columns:
                column_specs.append(
                    f"{col_name} OPTIONS (fpp={fpp}, numItems={num_items})"
                )
            
            sql = f"""
            CREATE BLOOM FILTER INDEX
            ON TABLE {table_name}
            FOR COLUMNS({', '.join(column_specs)})
            """
            
            self.spark.sql(sql)
            
            return {
                "table": table_name,
                "columns": columns,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error creating bloom filter on {table_name}: {str(e)}")
            return {"error": str(e)}
    
    def get_table_stats(self, table_name: str) -> Dict:
        """
        Get statistics about a Delta table.
        
        Args:
            table_name: Full table name
            
        Returns:
            Dictionary with table statistics
        """
        try:
            # Get table details
            details = self.spark.sql(f"DESCRIBE DETAIL {table_name}").collect()[0]
            
            # Get table size
            size_bytes = details.get("sizeInBytes", 0)
            num_files = details.get("numFiles", 0)
            
            # Get partition info
            partitions = self.spark.sql(f"SHOW PARTITIONS {table_name}").count()
            
            return {
                "table": table_name,
                "size_bytes": size_bytes,
                "size_gb": size_bytes / (1024 ** 3),
                "num_files": num_files,
                "num_partitions": partitions,
                "avg_file_size_mb": (size_bytes / num_files) / (1024 ** 2) if num_files > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting stats for {table_name}: {str(e)}")
            return {"error": str(e)}


class SparkConfigOptimizer:
    """
    Utility class for optimizing Spark configurations.
    """
    
    def __init__(self, spark: SparkSession):
        self.spark = spark
    
    def enable_adaptive_query_execution(self):
        """Enable Adaptive Query Execution (AQE)."""
        configs = {
            "spark.sql.adaptive.enabled": "true",
            "spark.sql.adaptive.coalescePartitions.enabled": "true",
            "spark.sql.adaptive.skewJoin.enabled": "true",
            "spark.sql.adaptive.localShuffleReader.enabled": "true",
            "spark.sql.adaptive.advisoryPartitionSizeInBytes": "64MB"
        }
        
        for key, value in configs.items():
            self.spark.conf.set(key, value)
        
        logger.info("Adaptive Query Execution enabled")
    
    def enable_delta_optimizations(self):
        """Enable Delta Lake auto-optimizations."""
        configs = {
            "spark.databricks.delta.optimizeWrite.enabled": "true",
            "spark.databricks.delta.autoCompact.enabled": "true",
            "spark.databricks.delta.autoCompact.targetFileSize": "128MB"
        }
        
        for key, value in configs.items():
            self.spark.conf.set(key, value)
        
        logger.info("Delta Lake optimizations enabled")
    
    def enable_delta_cache(self, max_disk_usage: str = "50g", 
                          max_metadata_cache: str = "1g"):
        """Enable Delta cache."""
        configs = {
            "spark.databricks.io.cache.enabled": "true",
            "spark.databricks.io.cache.maxDiskUsage": max_disk_usage,
            "spark.databricks.io.cache.maxMetaDataCache": max_metadata_cache
        }
        
        for key, value in configs.items():
            self.spark.conf.set(key, value)
        
        logger.info("Delta cache enabled")
    
    def tune_shuffle_partitions(self, num_partitions: int = 200):
        """Tune shuffle partitions based on data size."""
        self.spark.conf.set("spark.sql.shuffle.partitions", str(num_partitions))
        self.spark.conf.set("spark.default.parallelism", str(num_partitions))
        
        logger.info(f"Shuffle partitions set to {num_partitions}")
    
    def enable_dynamic_partition_pruning(self):
        """Enable dynamic partition pruning."""
        configs = {
            "spark.sql.optimizer.dynamicPartitionPruning.enabled": "true",
            "spark.sql.optimizer.dynamicPartitionPruning.useStats": "true",
            "spark.sql.optimizer.dynamicPartitionPruning.fallbackFilterRatio": "0.5"
        }
        
        for key, value in configs.items():
            self.spark.conf.set(key, value)
        
        logger.info("Dynamic partition pruning enabled")
    
    def optimize_for_streaming(self, max_files_per_trigger: int = 100):
        """Optimize configurations for streaming workloads."""
        configs = {
            "spark.sql.streaming.schemaInference": "true",
            "spark.sql.streaming.checkpointLocation": "s3://databricks-lakehouse/checkpoints/",
            "spark.sql.streaming.fileSource.schema.forceNullable": "true"
        }
        
        for key, value in configs.items():
            self.spark.conf.set(key, value)
        
        logger.info("Streaming optimizations enabled")
    
    def apply_all_optimizations(self, 
                               num_shuffle_partitions: int = 200,
                               enable_cache: bool = True):
        """Apply all performance optimizations."""
        self.enable_adaptive_query_execution()
        self.enable_delta_optimizations()
        self.enable_dynamic_partition_pruning()
        self.tune_shuffle_partitions(num_shuffle_partitions)
        
        if enable_cache:
            self.enable_delta_cache()
        
        logger.info("All performance optimizations applied")


def optimize_table_routine(spark: SparkSession, 
                          table_name: str,
                          z_order_cols: Optional[List[str]] = None,
                          vacuum_retention_hours: int = 168) -> Dict:
    """
    Complete optimization routine for a Delta table.
    
    Args:
        spark: SparkSession
        table_name: Full table name
        z_order_cols: Optional columns for Z-ordering
        vacuum_retention_hours: Hours to retain for VACUUM
        
    Returns:
        Dictionary with optimization results
    """
    optimizer = DeltaTableOptimizer(spark)
    
    results = {
        "table": table_name,
        "optimize": optimizer.optimize_table(table_name, z_order_cols=z_order_cols),
        "vacuum": optimizer.vacuum_table(table_name, vacuum_retention_hours),
        "stats_before": optimizer.get_table_stats(table_name)
    }
    
    # Get stats after optimization
    results["stats_after"] = optimizer.get_table_stats(table_name)
    
    return results

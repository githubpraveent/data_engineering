"""
Data quality check functions for Databricks notebooks.
Contains reusable quality check functions.
"""

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, count, when, isnan, isnull, countDistinct, sum as spark_sum
from typing import Dict, List, Optional, Tuple
import logging

def setup_logging():
    """Setup logging."""
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(__name__)

logger = setup_logging()

def check_not_null(df: DataFrame, column_name: str) -> Tuple[bool, int]:
    """
    Check if a column has null values.
    
    Args:
        df: Input DataFrame
        column_name: Column to check
        
    Returns:
        Tuple of (passed, null_count)
    """
    null_count = df.filter(col(column_name).isNull()).count()
    passed = null_count == 0
    return passed, null_count

def check_unique(df: DataFrame, column_name: str) -> Tuple[bool, int]:
    """
    Check if a column has unique values.
    
    Args:
        df: Input DataFrame
        column_name: Column to check
        
    Returns:
        Tuple of (passed, duplicate_count)
    """
    total_count = df.count()
    distinct_count = df.select(column_name).distinct().count()
    duplicate_count = total_count - distinct_count
    passed = duplicate_count == 0
    return passed, duplicate_count

def check_value_range(df: DataFrame, column_name: str, min_value: Optional[float] = None, 
                     max_value: Optional[float] = None) -> Tuple[bool, int]:
    """
    Check if values in a column are within a range.
    
    Args:
        df: Input DataFrame
        column_name: Column to check
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        
    Returns:
        Tuple of (passed, violation_count)
    """
    violations = df.filter(
        (col(column_name).isNull()) |
        ((min_value is not None) & (col(column_name) < min_value)) |
        ((max_value is not None) & (col(column_name) > max_value))
    ).count()
    passed = violations == 0
    return passed, violations

def check_value_in_list(df: DataFrame, column_name: str, allowed_values: List) -> Tuple[bool, int]:
    """
    Check if values in a column are in an allowed list.
    
    Args:
        df: Input DataFrame
        column_name: Column to check
        allowed_values: List of allowed values
        
    Returns:
        Tuple of (passed, violation_count)
    """
    violations = df.filter(
        (col(column_name).isNull()) | (~col(column_name).isin(allowed_values))
    ).count()
    passed = violations == 0
    return passed, violations

def check_referential_integrity(df_fact: DataFrame, df_dimension: DataFrame, 
                               fact_key: str, dim_key: str) -> Tuple[bool, int]:
    """
    Check referential integrity between fact and dimension tables.
    
    Args:
        df_fact: Fact table DataFrame
        df_fact: Dimension table DataFrame
        fact_key: Foreign key column in fact table
        dim_key: Primary key column in dimension table
        
    Returns:
        Tuple of (passed, orphan_count)
    """
    dim_keys = df_dimension.select(dim_key).distinct()
    orphans = df_fact.join(dim_keys, df_fact[fact_key] == dim_keys[dim_key], "left_anti").count()
    passed = orphans == 0
    return passed, orphans

def check_row_count(df: DataFrame, min_rows: Optional[int] = None, 
                   max_rows: Optional[int] = None) -> Tuple[bool, int]:
    """
    Check if row count is within expected range.
    
    Args:
        df: Input DataFrame
        min_rows: Minimum expected rows
        max_rows: Maximum expected rows
        
    Returns:
        Tuple of (passed, row_count)
    """
    row_count = df.count()
    passed = True
    
    if min_rows is not None and row_count < min_rows:
        passed = False
    if max_rows is not None and row_count > max_rows:
        passed = False
        
    return passed, row_count

def check_data_freshness(df: DataFrame, timestamp_column: str, 
                        max_age_hours: int) -> Tuple[bool, int]:
    """
    Check if data is fresh (recently updated).
    
    Args:
        df: Input DataFrame
        timestamp_column: Timestamp column to check
        max_age_hours: Maximum age in hours
        
    Returns:
        Tuple of (passed, stale_row_count)
    """
    from pyspark.sql.functions import current_timestamp, hours_between
    
    stale_count = df.filter(
        hours_between(col(timestamp_column), current_timestamp()) > max_age_hours
    ).count()
    passed = stale_count == 0
    return passed, stale_count

def run_quality_checks(df: DataFrame, checks: Dict) -> Dict:
    """
    Run multiple quality checks and return results.
    
    Args:
        df: Input DataFrame
        checks: Dictionary of check configurations
        
    Returns:
        Dictionary of check results
    """
    results = {}
    
    for check_name, check_config in checks.items():
        check_type = check_config.get("type")
        
        try:
            if check_type == "not_null":
                column = check_config["column"]
                passed, count = check_not_null(df, column)
                results[check_name] = {
                    "passed": passed,
                    "count": count,
                    "message": f"Not null check on {column}: {count} nulls found"
                }
                
            elif check_type == "unique":
                column = check_config["column"]
                passed, count = check_unique(df, column)
                results[check_name] = {
                    "passed": passed,
                    "count": count,
                    "message": f"Unique check on {column}: {count} duplicates found"
                }
                
            elif check_type == "value_range":
                column = check_config["column"]
                min_val = check_config.get("min")
                max_val = check_config.get("max")
                passed, count = check_value_range(df, column, min_val, max_val)
                results[check_name] = {
                    "passed": passed,
                    "count": count,
                    "message": f"Value range check on {column}: {count} violations found"
                }
                
            elif check_type == "value_in_list":
                column = check_config["column"]
                allowed = check_config["allowed_values"]
                passed, count = check_value_in_list(df, column, allowed)
                results[check_name] = {
                    "passed": passed,
                    "count": count,
                    "message": f"Value in list check on {column}: {count} violations found"
                }
                
            elif check_type == "row_count":
                min_rows = check_config.get("min_rows")
                max_rows = check_config.get("max_rows")
                passed, count = check_row_count(df, min_rows, max_rows)
                results[check_name] = {
                    "passed": passed,
                    "count": count,
                    "message": f"Row count check: {count} rows (expected {min_rows}-{max_rows})"
                }
                
            else:
                results[check_name] = {
                    "passed": False,
                    "message": f"Unknown check type: {check_type}"
                }
                
        except Exception as e:
            results[check_name] = {
                "passed": False,
                "message": f"Error running check: {str(e)}"
            }
    
    return results

def validate_all_checks_passed(results: Dict) -> bool:
    """
    Validate that all checks passed.
    
    Args:
        results: Dictionary of check results
        
    Returns:
        True if all checks passed, False otherwise
    """
    return all(check.get("passed", False) for check in results.values())


"""
Data Quality Utilities
Provides reusable functions for data quality checks across the medallion layers.
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, when, count, avg, sum as spark_sum,
    countDistinct, isnan, isnull, expr
)
from pyspark.sql.types import StructType
from typing import Dict, List, Tuple


class DataQualityChecker:
    """
    Comprehensive data quality checking utility.
    """
    
    def __init__(self, df: DataFrame):
        self.df = df
    
    def check_completeness(self, columns: List[str]) -> Dict[str, float]:
        """
        Check completeness (non-null rate) for specified columns.
        
        Args:
            columns: List of column names to check
            
        Returns:
            Dictionary mapping column names to completeness scores (0-1)
        """
        total_rows = self.df.count()
        if total_rows == 0:
            return {col: 0.0 for col in columns}
        
        completeness = {}
        for column in columns:
            non_null_count = self.df.filter(col(column).isNotNull()).count()
            completeness[column] = non_null_count / total_rows
        
        return completeness
    
    def check_uniqueness(self, columns: List[str]) -> Dict[str, float]:
        """
        Check uniqueness (distinct count / total count) for specified columns.
        
        Args:
            columns: List of column names to check
            
        Returns:
            Dictionary mapping column names to uniqueness scores (0-1)
        """
        total_rows = self.df.count()
        if total_rows == 0:
            return {col: 0.0 for col in columns}
        
        uniqueness = {}
        for column in columns:
            distinct_count = self.df.select(column).distinct().count()
            uniqueness[column] = distinct_count / total_rows
        
        return uniqueness
    
    def check_validity(self, rules: Dict[str, str]) -> Dict[str, Tuple[int, float]]:
        """
        Check validity using SQL expressions.
        
        Args:
            rules: Dictionary mapping rule names to SQL expressions
                  Example: {"positive_amount": "amount >= 0"}
        
        Returns:
            Dictionary mapping rule names to (violation_count, violation_rate)
        """
        total_rows = self.df.count()
        if total_rows == 0:
            return {rule: (0, 0.0) for rule in rules.keys()}
        
        validity = {}
        for rule_name, expression in rules.items():
            violations = self.df.filter(~expr(expression)).count()
            violation_rate = violations / total_rows
            validity[rule_name] = (violations, violation_rate)
        
        return validity
    
    def check_consistency(self, column_pairs: List[Tuple[str, str, str]]) -> Dict[str, float]:
        """
        Check consistency between related columns.
        
        Args:
            column_pairs: List of tuples (col1, col2, relationship)
                        Example: [("start_date", "end_date", "start < end")]
        
        Returns:
            Dictionary mapping relationships to consistency scores
        """
        total_rows = self.df.count()
        if total_rows == 0:
            return {}
        
        consistency = {}
        for col1, col2, relationship in column_pairs:
            if relationship == "col1 < col2":
                violations = self.df.filter(col(col1) >= col(col2)).count()
            elif relationship == "col1 <= col2":
                violations = self.df.filter(col(col1) > col(col2)).count()
            else:
                # Custom expression
                violations = self.df.filter(~expr(relationship)).count()
            
            consistency[f"{col1}_{col2}"] = 1.0 - (violations / total_rows)
        
        return consistency
    
    def generate_quality_report(self, 
                               key_columns: List[str] = None,
                               validation_rules: Dict[str, str] = None) -> Dict:
        """
        Generate comprehensive quality report.
        
        Args:
            key_columns: Columns to check for completeness and uniqueness
            validation_rules: Dictionary of validation rules
            
        Returns:
            Complete quality report dictionary
        """
        report = {
            "total_rows": self.df.count(),
            "total_columns": len(self.df.columns)
        }
        
        if key_columns:
            report["completeness"] = self.check_completeness(key_columns)
            report["uniqueness"] = self.check_uniqueness(key_columns)
        
        if validation_rules:
            validity_results = self.check_validity(validation_rules)
            report["validity"] = {
                rule: {
                    "violations": count,
                    "violation_rate": rate
                }
                for rule, (count, rate) in validity_results.items()
            }
        
        # Calculate overall quality score
        if "completeness" in report and "validity" in report:
            avg_completeness = sum(report["completeness"].values()) / len(report["completeness"])
            avg_validity = 1.0 - sum(
                v["violation_rate"] for v in report["validity"].values()
            ) / len(report["validity"])
            report["overall_quality_score"] = (avg_completeness + avg_validity) / 2
        elif "completeness" in report:
            report["overall_quality_score"] = sum(report["completeness"].values()) / len(report["completeness"])
        else:
            report["overall_quality_score"] = 1.0
        
        return report


def validate_schema(df: DataFrame, expected_schema: StructType) -> Tuple[bool, List[str]]:
    """
    Validate DataFrame schema against expected schema.
    
    Args:
        df: DataFrame to validate
        expected_schema: Expected StructType schema
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    actual_schema = df.schema
    
    # Check field names and types
    expected_fields = {f.name: f.dataType for f in expected_schema.fields}
    actual_fields = {f.name: f.dataType for f in actual_schema.fields}
    
    # Check for missing fields
    for field_name, field_type in expected_fields.items():
        if field_name not in actual_fields:
            errors.append(f"Missing field: {field_name}")
        elif actual_fields[field_name] != field_type:
            errors.append(
                f"Type mismatch for {field_name}: "
                f"expected {field_type}, got {actual_fields[field_name]}"
            )
    
    # Check for extra fields (warning, not error)
    for field_name in actual_fields:
        if field_name not in expected_fields:
            errors.append(f"Unexpected field: {field_name} (warning)")
    
    return len([e for e in errors if "warning" not in e]) == 0, errors

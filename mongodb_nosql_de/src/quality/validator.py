"""
Data Quality Validator

Validates data quality including schema, completeness, accuracy, and uniqueness.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Set
from loguru import logger

from config.settings import Settings


@dataclass
class ValidationResult:
    """Data quality validation result"""
    passed: bool
    quality_score: float
    error_message: Optional[str] = None
    invalid_records: Set[str] = None
    issues: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.invalid_records is None:
            self.invalid_records = set()
        if self.issues is None:
            self.issues = []


class DataQualityValidator:
    """Validates data quality according to configured rules"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.required_fields = ["transaction_id", "timestamp", "product_id", "total_amount"]
        self.numeric_fields = ["quantity", "unit_price", "total_amount"]

    def validate(self, data: List[Dict[str, Any]]) -> ValidationResult:
        """Validate data quality"""
        logger.info(f"Validating {len(data)} records")

        issues = []
        invalid_records = set()
        total_checks = 0
        passed_checks = 0

        # Schema validation
        schema_result = self._validate_schema(data)
        total_checks += schema_result["total"]
        passed_checks += schema_result["passed"]
        issues.extend(schema_result["issues"])
        invalid_records.update(schema_result["invalid_records"])

        # Completeness validation
        completeness_result = self._validate_completeness(data)
        total_checks += completeness_result["total"]
        passed_checks += completeness_result["passed"]
        issues.extend(completeness_result["issues"])

        # Accuracy validation
        accuracy_result = self._validate_accuracy(data)
        total_checks += accuracy_result["total"]
        passed_checks += accuracy_result["passed"]
        issues.extend(accuracy_result["issues"])
        invalid_records.update(accuracy_result["invalid_records"])

        # Uniqueness validation
        uniqueness_result = self._validate_uniqueness(data)
        total_checks += uniqueness_result["total"]
        passed_checks += uniqueness_result["passed"]
        issues.extend(uniqueness_result["issues"])
        invalid_records.update(uniqueness_result["invalid_records"])

        # Calculate quality score
        quality_score = passed_checks / total_checks if total_checks > 0 else 0.0

        # Determine if validation passed
        passed = (
            quality_score >= self.settings.dq_completeness_threshold and
            quality_score >= self.settings.dq_accuracy_threshold and
            quality_score >= self.settings.dq_uniqueness_threshold
        )

        error_message = None
        if not passed:
            error_message = f"Quality score {quality_score:.2%} below thresholds. Issues: {len(issues)}"

        logger.info(f"Validation complete: Score={quality_score:.2%}, Passed={passed}, Issues={len(issues)}")

        return ValidationResult(
            passed=passed,
            quality_score=quality_score,
            error_message=error_message,
            invalid_records=invalid_records,
            issues=issues[:10]  # Limit issues to first 10
        )

    def _validate_schema(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate data schema"""
        issues = []
        invalid_records = set()
        total = len(data) * len(self.required_fields)
        passed = 0

        for record in data:
            record_id = record.get("_id", "unknown")
            
            for field in self.required_fields:
                if field in record and record[field] is not None:
                    passed += 1
                else:
                    issues.append({
                        "type": "schema",
                        "record_id": record_id,
                        "field": field,
                        "message": f"Required field '{field}' is missing or null"
                    })
                    invalid_records.add(record_id)

        return {
            "total": total,
            "passed": passed,
            "issues": issues,
            "invalid_records": invalid_records
        }

    def _validate_completeness(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate data completeness"""
        issues = []
        total = len(data)
        passed = 0

        for record in data:
            non_null_fields = sum(1 for v in record.values() if v is not None and v != "")
            total_fields = len(record)
            completeness = non_null_fields / total_fields if total_fields > 0 else 0.0

            if completeness >= self.settings.dq_completeness_threshold:
                passed += 1
            else:
                record_id = record.get("_id", "unknown")
                issues.append({
                    "type": "completeness",
                    "record_id": record_id,
                    "completeness": completeness,
                    "message": f"Record completeness {completeness:.2%} below threshold"
                })

        return {
            "total": total,
            "passed": passed,
            "issues": issues,
            "invalid_records": set()
        }

    def _validate_accuracy(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate data accuracy (numeric fields, data types)"""
        issues = []
        invalid_records = set()
        total = len(data) * len(self.numeric_fields)
        passed = 0

        for record in data:
            record_id = record.get("_id", "unknown")
            
            # Check numeric fields
            for field in self.numeric_fields:
                if field in record:
                    value = record[field]
                    if isinstance(value, (int, float)) and value >= 0:
                        passed += 1
                    else:
                        issues.append({
                            "type": "accuracy",
                            "record_id": record_id,
                            "field": field,
                            "value": value,
                            "message": f"Field '{field}' must be a non-negative number"
                        })
                        invalid_records.add(record_id)
                else:
                    passed += 1  # Field not required, count as passed

            # Validate calculated fields
            if "total_amount" in record and "quantity" in record and "unit_price" in record:
                calculated = record.get("quantity", 0) * record.get("unit_price", 0)
                actual = record.get("total_amount", 0)
                
                # Allow small floating point differences
                if abs(calculated - actual) > 0.01:
                    issues.append({
                        "type": "accuracy",
                        "record_id": record_id,
                        "field": "total_amount",
                        "calculated": calculated,
                        "actual": actual,
                        "message": f"total_amount doesn't match quantity * unit_price"
                    })
                    invalid_records.add(record_id)

        return {
            "total": total,
            "passed": passed,
            "issues": issues,
            "invalid_records": invalid_records
        }

    def _validate_uniqueness(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate record uniqueness"""
        issues = []
        invalid_records = set()
        
        # Check for duplicate transaction IDs
        transaction_ids = {}
        for record in data:
            record_id = record.get("_id", "unknown")
            tx_id = record.get("transaction_id")
            
            if tx_id:
                if tx_id in transaction_ids:
                    issues.append({
                        "type": "uniqueness",
                        "record_id": record_id,
                        "transaction_id": tx_id,
                        "message": f"Duplicate transaction_id: {tx_id}"
                    })
                    invalid_records.add(record_id)
                    invalid_records.add(transaction_ids[tx_id])
                else:
                    transaction_ids[tx_id] = record_id

        total = len(data)
        passed = total - len(invalid_records)

        return {
            "total": total,
            "passed": passed,
            "issues": issues,
            "invalid_records": invalid_records
        }

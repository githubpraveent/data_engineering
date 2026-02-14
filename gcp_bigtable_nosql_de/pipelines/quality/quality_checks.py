"""
Data Quality Checks
Validates data schema, detects duplicates, and checks data quality
"""

import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
import hashlib
import json

logger = logging.getLogger(__name__)


class DataQualityChecker:
    """
    Data quality checker for event data
    """

    def __init__(
        self,
        required_fields: Optional[List[str]] = None,
        schema: Optional[Dict[str, type]] = None,
        check_duplicates: bool = True,
    ):
        """
        Initialize data quality checker

        Args:
            required_fields: List of required field names
            schema: Dictionary mapping field names to expected types
            check_duplicates: Enable duplicate detection
        """
        self.required_fields = required_fields or ["user_id", "event_id"]
        self.schema = schema or {}
        self.check_duplicates = check_duplicates
        self.seen_events: Set[str] = set()

        # Default schema for common fields
        self.default_schema = {
            "user_id": str,
            "event_id": str,
            "timestamp": datetime,
        }

    def _generate_event_hash(self, event: Dict[str, Any]) -> str:
        """
        Generate a hash for an event to detect duplicates

        Args:
            event: Event dictionary

        Returns:
            MD5 hash string
        """
        # Create a deterministic representation of the event
        key_fields = {
            "user_id": event.get("user_id"),
            "event_id": event.get("event_id"),
            "timestamp": event.get("timestamp"),
        }
        event_str = json.dumps(key_fields, sort_keys=True, default=str)
        return hashlib.md5(event_str.encode("utf-8")).hexdigest()

    def _validate_schema(self, event: Dict[str, Any]) -> List[str]:
        """
        Validate event schema

        Args:
            event: Event dictionary

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check required fields
        for field in self.required_fields:
            if field not in event:
                errors.append(f"Missing required field: {field}")

        # Validate field types
        for field, expected_type in {**self.default_schema, **self.schema}.items():
            if field in event:
                value = event[field]
                if expected_type == datetime:
                    # Special handling for datetime
                    if not isinstance(value, datetime):
                        try:
                            if isinstance(value, str):
                                datetime.fromisoformat(value.replace("Z", "+00:00"))
                        except (ValueError, AttributeError):
                            errors.append(
                                f"Field {field} is not a valid datetime: {value}"
                            )
                elif expected_type == int:
                    try:
                        int(value)
                    except (ValueError, TypeError):
                        errors.append(f"Field {field} is not an integer: {value}")
                elif expected_type == float:
                    try:
                        float(value)
                    except (ValueError, TypeError):
                        errors.append(f"Field {field} is not a float: {value}")
                elif not isinstance(value, expected_type):
                    errors.append(
                        f"Field {field} has wrong type: expected {expected_type.__name__}, "
                        f"got {type(value).__name__}"
                    )

        return errors

    def _check_duplicates(self, event: Dict[str, Any]) -> List[str]:
        """
        Check for duplicate events

        Args:
            event: Event dictionary

        Returns:
            List of errors (empty if no duplicates)
        """
        errors = []

        if not self.check_duplicates:
            return errors

        event_hash = self._generate_event_hash(event)

        if event_hash in self.seen_events:
            errors.append(
                f"Duplicate event detected: user_id={event.get('user_id')}, "
                f"event_id={event.get('event_id')}"
            )
        else:
            self.seen_events.add(event_hash)

        return errors

    def _check_missing_values(self, event: Dict[str, Any]) -> List[str]:
        """
        Check for missing or null values in required fields

        Args:
            event: Event dictionary

        Returns:
            List of errors
        """
        errors = []

        for field in self.required_fields:
            value = event.get(field)
            if value is None or (isinstance(value, str) and value.strip() == ""):
                errors.append(f"Field {field} is missing or empty")

        return errors

    def _check_data_range(self, event: Dict[str, Any]) -> List[str]:
        """
        Check data ranges and constraints

        Args:
            event: Event dictionary

        Returns:
            List of errors
        """
        errors = []

        # Check timestamp is not in the future
        timestamp = event.get("timestamp")
        if timestamp:
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    pass  # Already handled by schema validation

            if isinstance(timestamp, datetime):
                if timestamp > datetime.utcnow():
                    errors.append(f"Timestamp is in the future: {timestamp}")

        # Add more range checks as needed
        # e.g., user_id format, numeric ranges, etc.

        return errors

    def validate_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a single event

        Args:
            event: Event dictionary

        Returns:
            Dictionary with validation results:
            {
                "valid": bool,
                "errors": List[str],
                "warnings": List[str]
            }
        """
        all_errors = []
        warnings = []

        # Run all validation checks
        all_errors.extend(self._validate_schema(event))
        all_errors.extend(self._check_missing_values(event))
        all_errors.extend(self._check_data_range(event))
        all_errors.extend(self._check_duplicates(event))

        # Generate warnings for non-critical issues
        # e.g., optional fields with suspicious values

        result = {
            "valid": len(all_errors) == 0,
            "errors": all_errors,
            "warnings": warnings,
        }

        if not result["valid"]:
            logger.debug(
                f"Validation failed for event {event.get('event_id')}: {all_errors}"
            )

        return result

    def validate_batch(
        self, events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate a batch of events

        Args:
            events: List of event dictionaries

        Returns:
            Dictionary with batch validation results:
            {
                "total": int,
                "valid": int,
                "invalid": int,
                "errors": List[Dict]
            }
        """
        results = {
            "total": len(events),
            "valid": 0,
            "invalid": 0,
            "errors": [],
        }

        for event in events:
            validation_result = self.validate_event(event)
            if validation_result["valid"]:
                results["valid"] += 1
            else:
                results["invalid"] += 1
                results["errors"].append(
                    {
                        "event_id": event.get("event_id"),
                        "user_id": event.get("user_id"),
                        "errors": validation_result["errors"],
                    }
                )

        return results

    def reset_duplicate_cache(self):
        """Reset the duplicate detection cache"""
        self.seen_events.clear()
        logger.debug("Duplicate detection cache reset")

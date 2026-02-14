"""
Unit tests for data quality checks
"""

import pytest
from datetime import datetime, timedelta
from pipelines.quality.quality_checks import DataQualityChecker


class TestDataQualityChecker:
    """Test cases for DataQualityChecker"""

    def setup_method(self):
        """Setup test fixture"""
        self.checker = DataQualityChecker(
            required_fields=["user_id", "event_id"],
            check_duplicates=True,
        )

    def test_valid_event(self):
        """Test validation of a valid event"""
        event = {
            "user_id": "user123",
            "event_id": "event456",
            "timestamp": datetime.utcnow(),
            "event_type": "click",
        }

        result = self.checker.validate_event(event)
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_missing_required_field(self):
        """Test validation fails when required field is missing"""
        event = {
            "event_id": "event456",
            "timestamp": datetime.utcnow(),
        }

        result = self.checker.validate_event(event)
        assert result["valid"] is False
        assert any("user_id" in error for error in result["errors"])

    def test_duplicate_detection(self):
        """Test duplicate event detection"""
        event = {
            "user_id": "user123",
            "event_id": "event456",
            "timestamp": datetime.utcnow(),
        }

        # First occurrence should be valid
        result1 = self.checker.validate_event(event)
        assert result1["valid"] is True

        # Second occurrence should be detected as duplicate
        result2 = self.checker.validate_event(event)
        assert result2["valid"] is False
        assert any("Duplicate" in error for error in result2["errors"])

    def test_empty_user_id(self):
        """Test validation fails for empty user_id"""
        event = {
            "user_id": "",
            "event_id": "event456",
            "timestamp": datetime.utcnow(),
        }

        result = self.checker.validate_event(event)
        assert result["valid"] is False
        assert any("missing or empty" in error.lower() for error in result["errors"])

    def test_future_timestamp(self):
        """Test validation detects future timestamps"""
        future_time = datetime.utcnow() + timedelta(days=1)
        event = {
            "user_id": "user123",
            "event_id": "event456",
            "timestamp": future_time,
        }

        result = self.checker.validate_event(event)
        assert result["valid"] is False
        assert any("future" in error.lower() for error in result["errors"])

    def test_batch_validation(self):
        """Test batch validation"""
        events = [
            {
                "user_id": "user123",
                "event_id": "event1",
                "timestamp": datetime.utcnow(),
            },
            {
                "user_id": "user456",
                "event_id": "event2",
                "timestamp": datetime.utcnow(),
            },
            {
                "event_id": "event3",  # Missing user_id
                "timestamp": datetime.utcnow(),
            },
        ]

        result = self.checker.validate_batch(events)
        assert result["total"] == 3
        assert result["valid"] == 2
        assert result["invalid"] == 1
        assert len(result["errors"]) == 1

    def test_reset_duplicate_cache(self):
        """Test resetting duplicate cache"""
        event = {
            "user_id": "user123",
            "event_id": "event456",
            "timestamp": datetime.utcnow(),
        }

        # First occurrence
        result1 = self.checker.validate_event(event)
        assert result1["valid"] is True

        # Duplicate detected
        result2 = self.checker.validate_event(event)
        assert result2["valid"] is False

        # Reset cache
        self.checker.reset_duplicate_cache()

        # Should be valid again after reset
        result3 = self.checker.validate_event(event)
        assert result3["valid"] is True

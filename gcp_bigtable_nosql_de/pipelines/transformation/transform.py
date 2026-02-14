"""
Data Transformation Logic
Transforms and enriches raw event data before loading into Bigtable
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)


class EventTransformer:
    """
    Transforms raw event data for Bigtable storage
    """

    def __init__(self, enrich: bool = True):
        """
        Initialize transformer

        Args:
            enrich: Enable data enrichment
        """
        self.enrich = enrich

    def enrich_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich event with additional metadata

        Args:
            event: Raw event dictionary

        Returns:
            Enriched event dictionary
        """
        enriched = event.copy()

        # Add processing timestamp
        enriched["processed_at"] = datetime.utcnow().isoformat()

        # Add day of week, hour, etc. for time-based analysis
        timestamp = event.get("timestamp")
        if timestamp:
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    timestamp = None

            if isinstance(timestamp, datetime):
                enriched["day_of_week"] = timestamp.strftime("%A")
                enriched["hour"] = timestamp.hour
                enriched["date"] = timestamp.strftime("%Y-%m-%d")
                enriched["iso_week"] = timestamp.isocalendar()[1]
                enriched["month"] = timestamp.month
                enriched["year"] = timestamp.year

        # Add hash for deduplication
        if "user_id" in event and "event_id" in event:
            event_key = f"{event['user_id']}_{event['event_id']}"
            enriched["event_hash"] = hashlib.md5(
                event_key.encode("utf-8")
            ).hexdigest()

        # Normalize field names (e.g., camelCase to snake_case)
        enriched = self._normalize_field_names(enriched)

        return enriched

    def _normalize_field_names(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize field names to snake_case

        Args:
            event: Event dictionary

        Returns:
            Event with normalized field names
        """
        normalized = {}
        for key, value in event.items():
            # Convert camelCase to snake_case
            snake_key = self._camel_to_snake(key)
            normalized[snake_key] = value
        return normalized

    def _camel_to_snake(self, name: str) -> str:
        """Convert camelCase to snake_case"""
        import re

        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def transform(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform a raw event

        Args:
            raw_event: Raw event dictionary

        Returns:
            Transformed event dictionary
        """
        # Basic transformation
        transformed = raw_event.copy()

        # Enrich if enabled
        if self.enrich:
            transformed = self.enrich_event(transformed)

        # Clean and validate values
        transformed = self._clean_values(transformed)

        return transformed

    def _clean_values(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean and sanitize event values

        Args:
            event: Event dictionary

        Returns:
            Cleaned event dictionary
        """
        cleaned = {}

        for key, value in event.items():
            # Remove None values or convert to empty string
            if value is None:
                continue

            # Trim string values
            if isinstance(value, str):
                value = value.strip()
                if value == "":
                    continue

            # Convert numbers to appropriate types
            if isinstance(value, str):
                # Try to convert to int
                try:
                    if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
                        value = int(value)
                except (ValueError, AttributeError):
                    pass

                # Try to convert to float
                if isinstance(value, str):
                    try:
                        value = float(value)
                    except (ValueError, AttributeError):
                        pass

            cleaned[key] = value

        return cleaned

    def transform_batch(self, raw_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform a batch of events

        Args:
            raw_events: List of raw event dictionaries

        Returns:
            List of transformed event dictionaries
        """
        return [self.transform(event) for event in raw_events]


class EventAggregator:
    """
    Aggregates events for rollup tables
    """

    def __init__(self):
        """Initialize aggregator"""
        pass

    def aggregate_by_dimension(
        self, events: List[Dict[str, Any]], dimension: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Aggregate events by a dimension (e.g., user, song, product)

        Args:
            events: List of event dictionaries
            dimension: Dimension name to aggregate by

        Returns:
            Dictionary mapping dimension values to aggregated statistics
        """
        aggregates = {}

        for event in events:
            dim_value = event.get(dimension)
            if not dim_value:
                continue

            if dim_value not in aggregates:
                aggregates[dim_value] = {
                    "count": 0,
                    "dimension": dimension,
                    "dimension_value": dim_value,
                }

            aggregates[dim_value]["count"] += 1

            # Add more aggregations as needed
            # e.g., sum, average, min, max of numeric fields

        return aggregates

    def aggregate_by_time(
        self, events: List[Dict[str, Any]], time_period: str = "daily"
    ) -> Dict[str, Dict[str, Any]]:
        """
        Aggregate events by time period

        Args:
            events: List of event dictionaries
            time_period: Time period ('hourly', 'daily', 'weekly', 'monthly')

        Returns:
            Dictionary mapping time periods to aggregated statistics
        """
        aggregates = {}

        for event in events:
            timestamp = event.get("timestamp")
            if not timestamp:
                continue

            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    continue

            if not isinstance(timestamp, datetime):
                continue

            # Generate time period key
            if time_period == "hourly":
                period_key = timestamp.strftime("%Y-%m-%d-%H")
            elif time_period == "daily":
                period_key = timestamp.strftime("%Y-%m-%d")
            elif time_period == "weekly":
                # ISO week
                year, week, _ = timestamp.isocalendar()
                period_key = f"{year}-W{week:02d}"
            elif time_period == "monthly":
                period_key = timestamp.strftime("%Y-%m")
            else:
                raise ValueError(f"Unsupported time period: {time_period}")

            if period_key not in aggregates:
                aggregates[period_key] = {
                    "count": 0,
                    "time_period": time_period,
                    "period_key": period_key,
                }

            aggregates[period_key]["count"] += 1

        return aggregates

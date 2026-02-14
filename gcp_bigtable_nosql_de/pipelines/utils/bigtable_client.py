"""
Bigtable Client Utility
Provides a wrapper around Google Cloud Bigtable client for common operations
"""

import os
import logging
from typing import List, Dict, Optional, Any, Iterator
from datetime import datetime, timedelta
from google.cloud import bigtable
from google.cloud.bigtable import row_filters
from google.cloud.bigtable.row import PartialRowData
import struct

logger = logging.getLogger(__name__)


class BigTableClient:
    """
    Client for interacting with Google Cloud Bigtable
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        instance_id: Optional[str] = None,
        fact_table: str = "events_fact",
        aggregate_table: str = "events_aggregate",
    ):
        """
        Initialize Bigtable client

        Args:
            project_id: GCP project ID (defaults to environment variable)
            instance_id: Bigtable instance ID (defaults to environment variable)
            fact_table: Name of the fact table
            aggregate_table: Name of the aggregate table
        """
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
        self.instance_id = instance_id or os.getenv("BIGTABLE_INSTANCE")
        self.fact_table_name = fact_table
        self.aggregate_table_name = aggregate_table

        if not self.project_id or not self.instance_id:
            raise ValueError(
                "project_id and instance_id must be provided or set as environment variables"
            )

        # Initialize Bigtable client
        self.client = bigtable.Client(project=self.project_id, admin=True)
        self.instance = self.client.instance(self.instance_id)

        # Get table references
        self.fact_table = self.instance.table(self.fact_table_name)
        self.aggregate_table = self.instance.table(self.aggregate_table_name)

        logger.info(
            f"Initialized Bigtable client for project {self.project_id}, "
            f"instance {self.instance_id}"
        )

    def _encode_timestamp(self, timestamp: datetime) -> int:
        """Convert datetime to microseconds since epoch (Bigtable format)"""
        return int(timestamp.timestamp() * 1e6)

    def _decode_timestamp(self, timestamp_micros: int) -> datetime:
        """Convert Bigtable timestamp to datetime"""
        return datetime.fromtimestamp(timestamp_micros / 1e6)

    def _create_row_key(
        self, user_id: str, event_id: str, timestamp: Optional[datetime] = None
    ) -> bytes:
        """
        Create a row key for the fact table
        Format: {user_id}#{timestamp_reversed}#{event_id}
        This enables efficient range scans by user and time
        """
        if timestamp is None:
            timestamp = datetime.utcnow()

        # Reverse timestamp for chronological sorting (newest first)
        # Format: YYYYMMDDHHmmssSSSSSS (microseconds precision)
        timestamp_str = timestamp.strftime("%Y%m%d%H%M%S%f")
        timestamp_reversed = "".join(reversed(timestamp_str))

        # Row key: user_id#timestamp_reversed#event_id
        row_key = f"{user_id}#{timestamp_reversed}#{event_id}".encode("utf-8")
        return row_key

    def _create_aggregate_row_key(
        self, dimension: str, dimension_value: str, date: datetime
    ) -> bytes:
        """
        Create a row key for the aggregate table
        Format: {dimension}#{dimension_value}#{date}
        Examples: user#user123#20240115, song#song456#20240115
        """
        date_str = date.strftime("%Y%m%d")
        row_key = f"{dimension}#{dimension_value}#{date_str}".encode("utf-8")
        return row_key

    def write_event(
        self,
        user_id: str,
        event_id: str,
        event_data: Dict[str, Any],
        timestamp: Optional[datetime] = None,
    ) -> bool:
        """
        Write a single event to the fact table

        Args:
            user_id: User ID
            event_id: Unique event ID
            event_data: Dictionary of event data
            timestamp: Event timestamp (defaults to now)

        Returns:
            True if successful
        """
        try:
            if timestamp is None:
                timestamp = datetime.utcnow()

            row_key = self._create_row_key(user_id, event_id, timestamp)
            row = self.fact_table.direct_row(row_key)

            # Write event data to column family
            for key, value in event_data.items():
                if isinstance(value, (dict, list)):
                    import json

                    value = json.dumps(value)
                elif not isinstance(value, str):
                    value = str(value)

                row.set_cell(
                    "event_data",
                    key.encode("utf-8"),
                    value.encode("utf-8"),
                    timestamp=self._encode_timestamp(timestamp),
                )

            # Write metadata
            row.set_cell(
                "metadata",
                b"user_id",
                user_id.encode("utf-8"),
                timestamp=self._encode_timestamp(timestamp),
            )
            row.set_cell(
                "metadata",
                b"event_id",
                event_id.encode("utf-8"),
                timestamp=self._encode_timestamp(timestamp),
            )
            row.set_cell(
                "metadata",
                b"timestamp",
                timestamp.isoformat().encode("utf-8"),
                timestamp=self._encode_timestamp(timestamp),
            )
            row.set_cell(
                "quality",
                b"processed_at",
                datetime.utcnow().isoformat().encode("utf-8"),
                timestamp=self._encode_timestamp(timestamp),
            )

            # Commit the row
            row.commit()

            logger.debug(f"Wrote event {event_id} for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error writing event {event_id}: {str(e)}")
            raise

    def batch_write_events(
        self, events: List[Dict[str, Any]], batch_size: int = 100
    ) -> int:
        """
        Write multiple events in batches

        Args:
            events: List of event dictionaries with keys: user_id, event_id, event_data, timestamp
            batch_size: Number of events per batch

        Returns:
            Number of successfully written events
        """
        success_count = 0
        rows = []

        try:
            for event in events:
                user_id = event["user_id"]
                event_id = event["event_id"]
                event_data = event.get("event_data", {})
                timestamp = event.get("timestamp")

                if timestamp and isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp)

                row_key = self._create_row_key(user_id, event_id, timestamp)
                row = self.fact_table.direct_row(row_key)

                # Write event data
                for key, value in event_data.items():
                    if isinstance(value, (dict, list)):
                        import json

                        value = json.dumps(value)
                    elif not isinstance(value, str):
                        value = str(value)

                    row.set_cell(
                        "event_data",
                        key.encode("utf-8"),
                        value.encode("utf-8"),
                        timestamp=self._encode_timestamp(timestamp or datetime.utcnow()),
                    )

                # Write metadata
                row.set_cell(
                    "metadata",
                    b"user_id",
                    user_id.encode("utf-8"),
                )
                row.set_cell(
                    "metadata",
                    b"event_id",
                    event_id.encode("utf-8"),
                )

                rows.append(row)

                # Commit batch when reaching batch_size
                if len(rows) >= batch_size:
                    self.fact_table.mutate_rows(rows)
                    success_count += len(rows)
                    logger.debug(f"Committed batch of {len(rows)} events")
                    rows = []

            # Commit remaining rows
            if rows:
                self.fact_table.mutate_rows(rows)
                success_count += len(rows)
                logger.debug(f"Committed final batch of {len(rows)} events")

            logger.info(f"Successfully wrote {success_count} events")
            return success_count

        except Exception as e:
            logger.error(f"Error in batch write: {str(e)}")
            raise

    def get_user_events(
        self,
        user_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve events for a specific user

        Args:
            user_id: User ID to query
            start_time: Start time for range query
            end_time: End time for range query
            limit: Maximum number of events to return

        Returns:
            List of event dictionaries
        """
        try:
            # Create row key prefix for user
            row_key_prefix = f"{user_id}#".encode("utf-8")

            # Create row range
            if start_time and end_time:
                start_key = self._create_row_key(
                    user_id, "", start_time
                )  # Empty event_id for range
                end_key = self._create_row_key(user_id, "\xff", end_time)
            else:
                start_key = row_key_prefix
                end_key = row_key_prefix + b"\xff"

            # Read rows
            partial_rows = self.fact_table.read_rows(
                start_key=start_key, end_key=end_key, limit=limit
            )

            events = []
            for row in partial_rows:
                event = {"user_id": user_id, "row_key": row.row_key.decode("utf-8")}

                # Read event_data column family
                for column_family_id in row.cells:
                    for column, cells in row.cells[column_family_id].items():
                        column_name = column.decode("utf-8")
                        # Get the latest cell value
                        cell = cells[0]
                        value = cell.value.decode("utf-8")

                        if column_family_id == "event_data":
                            event[column_name] = value
                        elif column_family_id == "metadata":
                            event[f"metadata_{column_name}"] = value

                events.append(event)

            logger.debug(f"Retrieved {len(events)} events for user {user_id}")
            return events

        except Exception as e:
            logger.error(f"Error retrieving events for user {user_id}: {str(e)}")
            raise

    def write_aggregate(
        self,
        dimension: str,
        dimension_value: str,
        date: datetime,
        stats: Dict[str, Any],
    ) -> bool:
        """
        Write aggregate statistics to the aggregate table

        Args:
            dimension: Dimension name (e.g., 'user', 'song', 'product')
            dimension_value: Dimension value (e.g., 'user123', 'song456')
            date: Date for the aggregation
            stats: Dictionary of statistics

        Returns:
            True if successful
        """
        try:
            row_key = self._create_aggregate_row_key(dimension, dimension_value, date)
            row = self.aggregate_table.direct_row(row_key)

            # Determine column family based on aggregation period
            # For simplicity, using daily_stats for all
            column_family = "daily_stats"

            for key, value in stats.items():
                if isinstance(value, (dict, list)):
                    import json

                    value = json.dumps(value)
                elif isinstance(value, (int, float)):
                    # Encode numeric values as binary for efficient aggregation
                    value = struct.pack(">d", float(value))
                else:
                    value = str(value).encode("utf-8")

                if isinstance(value, bytes):
                    row.set_cell(column_family, key.encode("utf-8"), value)
                else:
                    row.set_cell(
                        column_family, key.encode("utf-8"), value.encode("utf-8")
                    )

            # Write metadata
            row.set_cell("metadata", b"dimension", dimension.encode("utf-8"))
            row.set_cell("metadata", b"dimension_value", dimension_value.encode("utf-8"))
            row.set_cell("metadata", b"date", date.strftime("%Y-%m-%d").encode("utf-8"))
            row.set_cell(
                "metadata",
                b"updated_at",
                datetime.utcnow().isoformat().encode("utf-8"),
            )

            row.commit()

            logger.debug(
                f"Wrote aggregate for {dimension}={dimension_value} on {date.strftime('%Y-%m-%d')}"
            )
            return True

        except Exception as e:
            logger.error(f"Error writing aggregate: {str(e)}")
            raise

    def get_daily_aggregates(
        self, dimension: str, dimension_value: str, date: datetime
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve daily aggregates for a dimension

        Args:
            dimension: Dimension name
            dimension_value: Dimension value
            date: Date to query

        Returns:
            Dictionary of aggregate statistics or None
        """
        try:
            row_key = self._create_aggregate_row_key(dimension, dimension_value, date)
            row = self.aggregate_table.read_row(row_key)

            if row is None:
                return None

            stats = {}
            for column_family_id in row.cells:
                if column_family_id == "daily_stats":
                    for column, cells in row.cells[column_family_id].items():
                        column_name = column.decode("utf-8")
                        cell = cells[0]
                        value = cell.value

                        # Try to decode as numeric, fallback to string
                        try:
                            stats[column_name] = struct.unpack(">d", value)[0]
                        except (struct.error, IndexError):
                            stats[column_name] = value.decode("utf-8")

            logger.debug(
                f"Retrieved aggregates for {dimension}={dimension_value} on {date.strftime('%Y-%m-%d')}"
            )
            return stats

        except Exception as e:
            logger.error(f"Error retrieving aggregates: {str(e)}")
            raise

    def close(self):
        """Close the Bigtable client"""
        # Bigtable client doesn't require explicit close, but included for completeness
        pass

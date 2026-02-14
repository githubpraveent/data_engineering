"""
Unit tests for Bigtable client
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pipelines.utils.bigtable_client import BigTableClient


class TestBigTableClient:
    """Test cases for BigTableClient"""

    @patch("pipelines.utils.bigtable_client.bigtable.Client")
    def setup_method(self, mock_client_class):
        """Setup test fixture"""
        mock_client = Mock()
        mock_instance = Mock()
        mock_fact_table = Mock()
        mock_aggregate_table = Mock()

        mock_client.instance.return_value = mock_instance
        mock_instance.table.return_value = mock_fact_table
        mock_instance.table.side_effect = lambda name: (
            mock_fact_table if name == "events_fact" else mock_aggregate_table
        )

        mock_client_class.return_value = mock_client

        self.client = BigTableClient(
            project_id="test-project", instance_id="test-instance"
        )
        self.mock_fact_table = mock_fact_table
        self.mock_aggregate_table = mock_aggregate_table

    def test_create_row_key(self):
        """Test row key creation"""
        user_id = "user123"
        event_id = "event456"
        timestamp = datetime(2024, 1, 15, 10, 30, 0)

        row_key = self.client._create_row_key(user_id, event_id, timestamp)

        assert isinstance(row_key, bytes)
        assert user_id.encode("utf-8") in row_key
        assert event_id.encode("utf-8") in row_key

    def test_create_aggregate_row_key(self):
        """Test aggregate row key creation"""
        dimension = "user"
        dimension_value = "user123"
        date = datetime(2024, 1, 15)

        row_key = self.client._create_aggregate_row_key(
            dimension, dimension_value, date
        )

        assert isinstance(row_key, bytes)
        assert dimension.encode("utf-8") in row_key
        assert dimension_value.encode("utf-8") in row_key

    def test_encode_decode_timestamp(self):
        """Test timestamp encoding and decoding"""
        original_time = datetime(2024, 1, 15, 10, 30, 45, 123456)

        encoded = self.client._encode_timestamp(original_time)
        decoded = self.client._decode_timestamp(encoded)

        # Check that decoded time is close to original (within microseconds)
        assert abs((decoded - original_time).total_seconds()) < 0.001

    @patch.object(BigTableClient, "_encode_timestamp")
    def test_write_event(self, mock_encode):
        """Test writing a single event"""
        mock_encode.return_value = 1234567890000000  # Microseconds

        mock_row = Mock()
        self.mock_fact_table.direct_row.return_value = mock_row

        success = self.client.write_event(
            user_id="user123",
            event_id="event456",
            event_data={"event_type": "click", "value": 100},
        )

        assert success is True
        assert mock_row.commit.called

    def test_batch_write_events(self):
        """Test batch writing events"""
        events = [
            {
                "user_id": "user1",
                "event_id": "event1",
                "event_data": {"type": "click"},
                "timestamp": datetime.utcnow(),
            },
            {
                "user_id": "user2",
                "event_id": "event2",
                "event_data": {"type": "view"},
                "timestamp": datetime.utcnow(),
            },
        ]

        # Mock mutate_rows to return success
        self.mock_fact_table.mutate_rows.return_value = None

        count = self.client.batch_write_events(events, batch_size=10)

        assert count == len(events)

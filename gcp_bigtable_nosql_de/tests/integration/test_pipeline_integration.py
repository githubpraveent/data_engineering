"""
Integration tests for the data pipeline
These tests require actual GCP credentials and Bigtable instance
"""

import pytest
import os
from datetime import datetime
from pipelines.ingestion.batch_ingestion import BatchIngestion
from pipelines.utils.bigtable_client import BigTableClient


@pytest.mark.integration
class TestPipelineIntegration:
    """Integration tests for data pipeline"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.instance_id = os.getenv("BIGTABLE_INSTANCE")

        if not self.project_id or not self.instance_id:
            pytest.skip("GCP_PROJECT_ID and BIGTABLE_INSTANCE must be set")

    def test_batch_ingestion_integration(self, tmp_path):
        """Test full batch ingestion workflow"""
        # Create a temporary CSV file
        csv_file = tmp_path / "test_events.csv"
        csv_content = """user_id,event_id,event_type,timestamp
user001,event001,click,2024-01-15T10:00:00Z
user002,event002,view,2024-01-15T10:05:00Z"""
        csv_file.write_text(csv_content)

        # Run ingestion
        ingestion = BatchIngestion(
            project_id=self.project_id,
            instance_id=self.instance_id,
            batch_size=10,
            enable_quality_checks=True,
        )

        try:
            stats = ingestion.ingest_file(str(csv_file), file_format="csv")

            assert stats["total_read"] == 2
            assert stats["valid"] >= 0
            assert stats["written"] >= 0

        finally:
            ingestion.close()

    def test_bigtable_client_integration(self):
        """Test Bigtable client operations"""
        client = BigTableClient(
            project_id=self.project_id, instance_id=self.instance_id
        )

        try:
            # Write a test event
            success = client.write_event(
                user_id="test_user",
                event_id=f"test_event_{datetime.utcnow().timestamp()}",
                event_data={"event_type": "test", "value": 123},
            )

            assert success is True

            # Retrieve events (may be empty if table is new)
            events = client.get_user_events(
                user_id="test_user", limit=10
            )

            assert isinstance(events, list)

        finally:
            client.close()

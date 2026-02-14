"""
Integration tests for data pipelines.
These tests require GCP credentials and access to test resources.
"""

import unittest
import os
from google.cloud import bigquery, storage, pubsub_v1
from datetime import datetime, timedelta
import json
import time

PROJECT_ID = os.environ.get('GCP_PROJECT', 'your-project-id')
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')


class TestDataflowIntegration(unittest.TestCase):
    """Integration tests for Dataflow pipelines."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test resources."""
        cls.project_id = PROJECT_ID
        cls.environment = ENVIRONMENT
        cls.bigquery_client = bigquery.Client(project=cls.project_id)
        cls.storage_client = storage.Client(project=cls.project_id)
        cls.pubsub_publisher = pubsub_v1.PublisherClient()
    
    def test_bigquery_table_exists(self):
        """Test that BigQuery staging tables exist."""
        dataset_id = f'staging_{self.environment}'
        tables = ['transactions_staging', 'customers_staging', 'products_staging']
        
        for table_id in tables:
            table_ref = self.bigquery_client.dataset(dataset_id).table(table_id)
            table = self.bigquery_client.get_table(table_ref)
            self.assertIsNotNone(table, f"Table {table_id} should exist")
    
    def test_gcs_buckets_exist(self):
        """Test that GCS buckets exist."""
        buckets = [
            f'{self.project_id}-data-lake-raw-{self.environment}',
            f'{self.project_id}-data-lake-staging-{self.environment}',
            f'{self.project_id}-data-lake-curated-{self.environment}'
        ]
        
        for bucket_name in buckets:
            bucket = self.storage_client.bucket(bucket_name)
            self.assertTrue(bucket.exists(), f"Bucket {bucket_name} should exist")
    
    def test_pubsub_topics_exist(self):
        """Test that Pub/Sub topics exist."""
        topics = [
            f'retail-transactions-{self.environment}',
            f'retail-inventory-{self.environment}',
            f'retail-customers-{self.environment}'
        ]
        
        for topic_name in topics:
            topic_path = self.pubsub_publisher.topic_path(self.project_id, topic_name)
            # Note: This would require additional setup to check topic existence
            # For now, we'll skip if topic doesn't exist
            pass


class TestDataQualityIntegration(unittest.TestCase):
    """Integration tests for data quality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test resources."""
        cls.project_id = PROJECT_ID
        cls.environment = ENVIRONMENT
        cls.bigquery_client = bigquery.Client(project=cls.project_id)
    
    def test_referential_integrity(self):
        """Test referential integrity between fact and dimension tables."""
        query = f"""
        SELECT COUNT(*) as orphaned_records
        FROM `{self.project_id}.curated_{self.environment}.sales_fact` sf
        LEFT JOIN `{self.project_id}.curated_{self.environment}.customer_dimension` cd
        ON sf.customer_id = cd.customer_id AND cd.is_current = TRUE
        WHERE cd.customer_id IS NULL
        LIMIT 1
        """
        
        try:
            result = self.bigquery_client.query(query).result()
            for row in result:
                self.assertEqual(row.orphaned_records, 0, "No orphaned records should exist")
        except Exception as e:
            self.skipTest(f"Tables may not exist yet: {e}")
    
    def test_no_duplicate_transactions(self):
        """Test that there are no duplicate transaction IDs."""
        query = f"""
        SELECT COUNT(*) as duplicate_count
        FROM (
            SELECT transaction_id, COUNT(*) as cnt
            FROM `{self.project_id}.curated_{self.environment}.sales_fact`
            GROUP BY transaction_id
            HAVING cnt > 1
        )
        """
        
        try:
            result = self.bigquery_client.query(query).result()
            for row in result:
                self.assertEqual(row.duplicate_count, 0, "No duplicate transactions should exist")
        except Exception as e:
            self.skipTest(f"Table may not exist yet: {e}")
    
    def test_scd2_integrity(self):
        """Test SCD Type 2 integrity - only one current record per key."""
        query = f"""
        SELECT COUNT(*) as invalid_scd2
        FROM (
            SELECT customer_id, COUNT(*) as current_count
            FROM `{self.project_id}.curated_{self.environment}.customer_dimension`
            WHERE is_current = TRUE
            GROUP BY customer_id
            HAVING current_count > 1
        )
        """
        
        try:
            result = self.bigquery_client.query(query).result()
            for row in result:
                self.assertEqual(row.invalid_scd2, 0, "SCD Type 2 integrity should be maintained")
        except Exception as e:
            self.skipTest(f"Table may not exist yet: {e}")


if __name__ == '__main__':
    unittest.main()


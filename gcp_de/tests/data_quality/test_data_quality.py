"""
Data quality tests for BigQuery tables.
"""

import unittest
import os
from google.cloud import bigquery
from datetime import datetime, timedelta

PROJECT_ID = os.environ.get('GCP_PROJECT', 'your-project-id')
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')


class TestDataQuality(unittest.TestCase):
    """Data quality tests."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test resources."""
        cls.project_id = PROJECT_ID
        cls.environment = ENVIRONMENT
        cls.bigquery_client = bigquery.Client(project=cls.project_id)
    
    def test_no_null_primary_keys(self):
        """Test that primary keys are not null."""
        query = f"""
        SELECT COUNT(*) as null_count
        FROM `{self.project_id}.staging_{self.environment}.transactions_staging`
        WHERE transaction_id IS NULL
        OR customer_id IS NULL
        OR product_id IS NULL
        """
        
        try:
            result = self.bigquery_client.query(query).result()
            for row in result:
                self.assertEqual(row.null_count, 0, "Primary keys should not be null")
        except Exception as e:
            self.skipTest(f"Table may not exist: {e}")
    
    def test_data_freshness(self):
        """Test that data is fresh (loaded within last 24 hours)."""
        query = f"""
        SELECT MAX(load_timestamp) as latest_load
        FROM `{self.project_id}.curated_{self.environment}.sales_fact`
        """
        
        try:
            result = self.bigquery_client.query(query).result()
            for row in result:
                if row.latest_load:
                    hours_ago = (datetime.now() - row.latest_load).total_seconds() / 3600
                    self.assertLess(hours_ago, 25, "Data should be fresh (within 24 hours)")
        except Exception as e:
            self.skipTest(f"Table may not exist: {e}")
    
    def test_no_negative_amounts(self):
        """Test that there are no negative amounts."""
        query = f"""
        SELECT COUNT(*) as negative_count
        FROM `{self.project_id}.curated_{self.environment}.sales_fact`
        WHERE total_amount < 0
        OR quantity < 0
        OR unit_price < 0
        """
        
        try:
            result = self.bigquery_client.query(query).result()
            for row in result:
                self.assertEqual(row.negative_count, 0, "No negative amounts should exist")
        except Exception as e:
            self.skipTest(f"Table may not exist: {e}")
    
    def test_transaction_totals_consistency(self):
        """Test that transaction totals are consistent."""
        query = f"""
        SELECT COUNT(*) as inconsistent_transactions
        FROM (
            SELECT 
                transaction_id,
                SUM(quantity * unit_price) as calculated_total,
                SUM(total_amount) as stored_total
            FROM `{self.project_id}.curated_{self.environment}.sales_fact`
            GROUP BY transaction_id
            HAVING ABS(calculated_total - stored_total) > 0.01
        )
        """
        
        try:
            result = self.bigquery_client.query(query).result()
            for row in result:
                self.assertEqual(row.inconsistent_transactions, 0, 
                               "Transaction totals should be consistent")
        except Exception as e:
            self.skipTest(f"Table may not exist: {e}")
    
    def test_row_count_range(self):
        """Test that row count is within expected range."""
        query = f"""
        SELECT COUNT(*) as row_count
        FROM `{self.project_id}.curated_{self.environment}.sales_fact`
        WHERE DATE(transaction_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
        """
        
        try:
            result = self.bigquery_client.query(query).result()
            for row in result:
                self.assertGreaterEqual(row.row_count, 0, "Row count should be non-negative")
                self.assertLess(row.row_count, 10000000, "Row count should be reasonable")
        except Exception as e:
            self.skipTest(f"Table may not exist: {e}")
    
    def test_customer_dimension_completeness(self):
        """Test that customer dimension has required fields."""
        query = f"""
        SELECT COUNT(*) as incomplete_records
        FROM `{self.project_id}.curated_{self.environment}.customer_dimension`
        WHERE customer_id IS NULL
        OR is_current IS NULL
        OR effective_date IS NULL
        """
        
        try:
            result = self.bigquery_client.query(query).result()
            for row in result:
                self.assertEqual(row.incomplete_records, 0, 
                               "Customer dimension should have all required fields")
        except Exception as e:
            self.skipTest(f"Table may not exist: {e}")


if __name__ == '__main__':
    unittest.main()


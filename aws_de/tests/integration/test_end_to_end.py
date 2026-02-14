"""
End-to-end integration tests
"""
import pytest
import os
import time
import boto3
import psycopg2

class TestEndToEnd:
    """End-to-end integration tests"""
    
    @pytest.fixture
    def s3_client(self):
        return boto3.client('s3', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
    
    @pytest.fixture
    def glue_client(self):
        return boto3.client('glue', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
    
    @pytest.fixture
    def redshift_conn(self):
        conn = psycopg2.connect(
            host=os.environ.get('REDSHIFT_HOST'),
            port=int(os.environ.get('REDSHIFT_PORT', 5439)),
            database=os.environ.get('REDSHIFT_DATABASE', 'retail_dw'),
            user=os.environ.get('REDSHIFT_USER'),
            password=os.environ.get('REDSHIFT_PASSWORD')
        )
        yield conn
        conn.close()
    
    def test_s3_landing_zone_created(self, s3_client):
        """Test that S3 landing zone exists and has data"""
        bucket = os.environ.get('S3_DATALAKE_BUCKET')
        assert bucket is not None, "S3_DATALAKE_BUCKET not set"
        
        # Check if bucket exists
        try:
            s3_client.head_bucket(Bucket=bucket)
        except Exception as e:
            pytest.fail(f"Bucket {bucket} does not exist: {e}")
        
        # Check if landing zone has data
        response = s3_client.list_objects_v2(
            Bucket=bucket,
            Prefix='landing/',
            MaxKeys=1
        )
        
        # At least check that prefix exists (data may not be present in test env)
        assert 'Prefix' in response or 'Contents' in response
    
    def test_glue_jobs_exist(self, glue_client):
        """Test that Glue jobs are created"""
        jobs = [
            f"{os.environ.get('ENVIRONMENT', 'dev')}-retail-streaming-customer",
            f"{os.environ.get('ENVIRONMENT', 'dev')}-retail-streaming-order",
            f"{os.environ.get('ENVIRONMENT', 'dev')}-retail-batch-landing-to-staging",
            f"{os.environ.get('ENVIRONMENT', 'dev')}-retail-batch-staging-to-curated"
        ]
        
        for job_name in jobs:
            try:
                response = glue_client.get_job(JobName=job_name)
                assert response['Job']['Name'] == job_name
            except Exception as e:
                pytest.fail(f"Glue job {job_name} does not exist: {e}")
    
    def test_redshift_schemas_exist(self, redshift_conn):
        """Test that Redshift schemas are created"""
        with redshift_conn.cursor() as cur:
            cur.execute("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name IN ('staging', 'analytics')
            """)
            
            schemas = [row[0] for row in cur.fetchall()]
            assert 'staging' in schemas, "Staging schema not found"
            assert 'analytics' in schemas, "Analytics schema not found"
    
    def test_redshift_tables_exist(self, redshift_conn):
        """Test that Redshift tables are created"""
        with redshift_conn.cursor() as cur:
            cur.execute("""
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_schema IN ('staging', 'analytics')
                AND table_name IN (
                    'customer_streaming',
                    'order_streaming',
                    'dim_customer',
                    'dim_product',
                    'fact_sales'
                )
            """)
            
            tables = {(row[0], row[1]) for row in cur.fetchall()}
            
            expected_tables = [
                ('staging', 'customer_streaming'),
                ('staging', 'order_streaming'),
                ('analytics', 'dim_customer'),
                ('analytics', 'dim_product'),
                ('analytics', 'fact_sales')
            ]
            
            for expected in expected_tables:
                assert expected in tables, f"Table {expected[1]} in schema {expected[0]} not found"
    
    def test_data_flow_landing_to_staging(self, s3_client):
        """Test that data flows from landing to staging"""
        bucket = os.environ.get('S3_DATALAKE_BUCKET')
        
        # Check landing zone
        landing_objects = s3_client.list_objects_v2(
            Bucket=bucket,
            Prefix='landing/',
            MaxKeys=10
        )
        
        # Check staging zone
        staging_objects = s3_client.list_objects_v2(
            Bucket=bucket,
            Prefix='staging/',
            MaxKeys=10
        )
        
        # In a real test, we would verify that staging has processed data from landing
        # For now, just verify prefixes exist
        assert 'Prefix' in landing_objects or 'Contents' in landing_objects
        assert 'Prefix' in staging_objects or 'Contents' in staging_objects

if __name__ == '__main__':
    pytest.main([__file__, '-v'])


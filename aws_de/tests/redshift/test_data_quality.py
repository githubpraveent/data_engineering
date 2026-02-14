"""
Test Redshift data quality and SCD behavior
"""
import pytest
import os
import psycopg2
from psycopg2.extras import RealDictCursor

class TestRedshiftDataQuality:
    """Test Redshift data quality and validation"""
    
    @pytest.fixture
    def redshift_conn(self):
        """Create Redshift connection"""
        conn = psycopg2.connect(
            host=os.environ.get('REDSHIFT_HOST'),
            port=int(os.environ.get('REDSHIFT_PORT', 5439)),
            database=os.environ.get('REDSHIFT_DATABASE', 'retail_dw'),
            user=os.environ.get('REDSHIFT_USER'),
            password=os.environ.get('REDSHIFT_PASSWORD')
        )
        yield conn
        conn.close()
    
    def test_scd_type2_current_flag(self, redshift_conn):
        """Test that SCD Type 2 has only one current record per customer"""
        with redshift_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT customer_id, COUNT(*) as current_count
                FROM analytics.dim_customer
                WHERE is_current = TRUE
                GROUP BY customer_id
                HAVING COUNT(*) > 1
            """)
            
            duplicates = cur.fetchall()
            assert len(duplicates) == 0, "Found customers with multiple current records"
    
    def test_scd_type2_effective_dates(self, redshift_conn):
        """Test that SCD Type 2 effective dates are valid"""
        with redshift_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT customer_id, effective_date, end_date, is_current
                FROM analytics.dim_customer
                WHERE (end_date IS NOT NULL AND end_date < effective_date)
                   OR (is_current = FALSE AND end_date IS NULL)
            """)
            
            invalid_dates = cur.fetchall()
            assert len(invalid_dates) == 0, "Found invalid effective/end dates"
    
    def test_referential_integrity_sales_customer(self, redshift_conn):
        """Test referential integrity between fact_sales and dim_customer"""
        with redshift_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT COUNT(*) as orphan_count
                FROM analytics.fact_sales fs
                LEFT JOIN analytics.dim_customer dc ON fs.customer_sk = dc.customer_sk
                WHERE dc.customer_sk IS NULL
            """)
            
            result = cur.fetchone()
            assert result['orphan_count'] == 0, "Found orphaned sales records"
    
    def test_referential_integrity_sales_product(self, redshift_conn):
        """Test referential integrity between fact_sales and dim_product"""
        with redshift_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT COUNT(*) as orphan_count
                FROM analytics.fact_sales fs
                LEFT JOIN analytics.dim_product dp ON fs.product_sk = dp.product_sk
                WHERE dp.product_sk IS NULL
            """)
            
            result = cur.fetchone()
            assert result['orphan_count'] == 0, "Found orphaned sales records"
    
    def test_referential_integrity_sales_date(self, redshift_conn):
        """Test referential integrity between fact_sales and dim_date"""
        with redshift_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT COUNT(*) as orphan_count
                FROM analytics.fact_sales fs
                LEFT JOIN analytics.dim_date dd ON fs.order_date_key = dd.date_key
                WHERE dd.date_key IS NULL
            """)
            
            result = cur.fetchone()
            assert result['orphan_count'] == 0, "Found orphaned sales records"
    
    def test_fact_sales_amounts(self, redshift_conn):
        """Test that sales amounts are non-negative"""
        with redshift_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT COUNT(*) as negative_count
                FROM analytics.fact_sales
                WHERE sales_amount < 0
                   OR net_sales_amount < 0
                   OR quantity < 0
            """)
            
            result = cur.fetchone()
            assert result['negative_count'] == 0, "Found negative sales amounts"
    
    def test_dimension_surrogate_keys(self, redshift_conn):
        """Test that dimension tables have unique surrogate keys"""
        with redshift_conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Test dim_customer
            cur.execute("""
                SELECT customer_sk, COUNT(*) as count
                FROM analytics.dim_customer
                GROUP BY customer_sk
                HAVING COUNT(*) > 1
            """)
            duplicates = cur.fetchall()
            assert len(duplicates) == 0, "Found duplicate customer_sk"
            
            # Test dim_product
            cur.execute("""
                SELECT product_sk, COUNT(*) as count
                FROM analytics.dim_product
                GROUP BY product_sk
                HAVING COUNT(*) > 1
            """)
            duplicates = cur.fetchall()
            assert len(duplicates) == 0, "Found duplicate product_sk"
    
    def test_data_freshness(self, redshift_conn):
        """Test that data is fresh (updated within last 24 hours)"""
        with redshift_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT MAX(created_at) as last_update
                FROM analytics.fact_sales
            """)
            
            result = cur.fetchone()
            if result['last_update']:
                from datetime import datetime, timedelta
                last_update = result['last_update']
                if isinstance(last_update, str):
                    from dateutil import parser
                    last_update = parser.parse(last_update)
                
                age = datetime.now() - last_update
                assert age < timedelta(days=1), f"Data is stale: last update was {age} ago"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])


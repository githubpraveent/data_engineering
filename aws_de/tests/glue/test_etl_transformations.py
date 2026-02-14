"""
Test Glue ETL transformation logic
"""
import pytest
import sys
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType, DecimalType
from pyspark.sql.functions import col

# Mock Glue context for testing
class MockGlueContext:
    def __init__(self, spark):
        self.spark = spark

class TestGlueTransformations:
    """Test Glue ETL transformation functions"""
    
    @pytest.fixture
    def spark(self):
        return SparkSession.builder \
            .appName("test") \
            .master("local[2]") \
            .getOrCreate()
    
    @pytest.fixture
    def sample_customer_data(self, spark):
        schema = StructType([
            StructField("operation", StringType(), True),
            StructField("customer_id", IntegerType(), True),
            StructField("customer_name", StringType(), True),
            StructField("email", StringType(), True),
            StructField("phone", StringType(), True),
            StructField("state", StringType(), True)
        ])
        
        data = [
            ("c", 1, "  John Doe  ", "JOHN@EXAMPLE.COM", "123-456-7890", "ny"),
            ("u", 2, "Jane Smith", "jane@example.com", "9876543210", "CA"),
            ("d", 3, "Bob Johnson", "bob@example.com", "555-1234", "tx")
        ]
        
        return spark.createDataFrame(data, schema)
    
    def test_customer_name_trim(self, sample_customer_data):
        """Test that customer names are trimmed"""
        from pyspark.sql.functions import trim
        
        result = sample_customer_data.withColumn("customer_name", trim(col("customer_name")))
        rows = result.collect()
        
        assert rows[0]["customer_name"] == "John Doe"
        assert rows[1]["customer_name"] == "Jane Smith"
    
    def test_email_lowercase(self, sample_customer_data):
        """Test that emails are lowercased"""
        from pyspark.sql.functions import lower
        
        result = sample_customer_data.withColumn("email", lower(col("email")))
        rows = result.collect()
        
        assert rows[0]["email"] == "john@example.com"
        assert rows[1]["email"] == "jane@example.com"
    
    def test_phone_cleaning(self, sample_customer_data):
        """Test phone number cleaning (remove non-digits)"""
        from pyspark.sql.functions import regexp_replace
        
        result = sample_customer_data.withColumn(
            "phone", 
            regexp_replace(col("phone"), "[^0-9]", "")
        )
        rows = result.collect()
        
        assert rows[0]["phone"] == "1234567890"
        assert rows[1]["phone"] == "9876543210"
    
    def test_state_uppercase(self, sample_customer_data):
        """Test that state codes are uppercased"""
        from pyspark.sql.functions import upper
        
        result = sample_customer_data.withColumn("state", upper(col("state")))
        rows = result.collect()
        
        assert rows[0]["state"] == "NY"
        assert rows[1]["state"] == "CA"
        assert rows[2]["state"] == "TX"
    
    def test_data_validation(self, spark):
        """Test data validation logic"""
        schema = StructType([
            StructField("customer_id", IntegerType(), True),
            StructField("customer_name", StringType(), True),
            StructField("email", StringType(), True),
            StructField("is_valid", StringType(), True)
        ])
        
        data = [
            (1, "John Doe", "john@example.com", None),
            (2, None, "jane@example.com", None),  # Missing name
            (3, "Bob", "invalid-email", None),  # Invalid email
            (4, "Alice", None, None)  # Missing email
        ]
        
        df = spark.createDataFrame(data, schema)
        
        from pyspark.sql.functions import when, lit
        
        validated_df = df.withColumn(
            "is_valid",
            when(
                col("customer_id").isNotNull() &
                col("customer_name").isNotNull() &
                col("email").isNotNull() &
                col("email").rlike("^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$"),
                lit(True)
            ).otherwise(lit(False))
        )
        
        rows = validated_df.collect()
        assert rows[0]["is_valid"] == True
        assert rows[1]["is_valid"] == False
        assert rows[2]["is_valid"] == False
        assert rows[3]["is_valid"] == False
    
    def test_deduplication(self, spark):
        """Test deduplication logic"""
        schema = StructType([
            StructField("customer_id", IntegerType(), True),
            StructField("change_timestamp", TimestampType(), True)
        ])
        
        from datetime import datetime
        
        data = [
            (1, datetime(2024, 1, 1, 10, 0, 0)),
            (1, datetime(2024, 1, 1, 11, 0, 0)),  # Duplicate
            (2, datetime(2024, 1, 1, 12, 0, 0)),
            (1, datetime(2024, 1, 1, 9, 0, 0))   # Older duplicate
        ]
        
        df = spark.createDataFrame(data, schema)
        
        from pyspark.sql.window import Window
        from pyspark.sql.functions import row_number
        
        window_spec = Window.partitionBy("customer_id").orderBy(col("change_timestamp").desc())
        deduplicated_df = df.withColumn("row_num", row_number().over(window_spec)) \
            .filter(col("row_num") == 1) \
            .drop("row_num")
        
        rows = deduplicated_df.collect()
        assert len(rows) == 2  # Should have 2 unique customers
        assert rows[0]["customer_id"] == 1
        assert rows[0]["change_timestamp"] == datetime(2024, 1, 1, 11, 0, 0)  # Latest

if __name__ == '__main__':
    pytest.main([__file__, '-v'])


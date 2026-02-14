-- Unity Catalog Configuration
-- Run this script to set up the catalog structure and permissions

-- Create main catalog
CREATE CATALOG IF NOT EXISTS lakehouse
COMMENT 'Main production catalog for lakehouse';

-- Create development catalog
CREATE CATALOG IF NOT EXISTS lakehouse_dev
COMMENT 'Development catalog for testing';

-- Use the main catalog
USE CATALOG lakehouse;

-- Create schemas for medallion architecture
CREATE SCHEMA IF NOT EXISTS bronze
COMMENT 'Bronze layer: Raw ingested data';

CREATE SCHEMA IF NOT EXISTS silver
COMMENT 'Silver layer: Cleaned and enriched data';

CREATE SCHEMA IF NOT EXISTS gold
COMMENT 'Gold layer: Analytics-ready aggregated data';

-- Grant permissions
-- Data Engineers: Full access to all layers
CREATE ROLE IF NOT EXISTS data_engineers;
GRANT ALL PRIVILEGES ON CATALOG lakehouse TO ROLE data_engineers;
GRANT ALL PRIVILEGES ON SCHEMA bronze TO ROLE data_engineers;
GRANT ALL PRIVILEGES ON SCHEMA silver TO ROLE data_engineers;
GRANT ALL PRIVILEGES ON SCHEMA gold TO ROLE data_engineers;

-- Data Analysts: Read-only access to Silver and Gold
CREATE ROLE IF NOT EXISTS data_analysts;
GRANT SELECT ON SCHEMA silver TO ROLE data_analysts;
GRANT SELECT ON SCHEMA gold TO ROLE data_analysts;

-- ML Engineers: Read Gold, write to ML schemas
CREATE ROLE IF NOT EXISTS ml_engineers;
GRANT SELECT ON SCHEMA gold TO ROLE ml_engineers;
GRANT ALL PRIVILEGES ON SCHEMA ml TO ROLE ml_engineers;

-- Create ML schema for model artifacts
CREATE SCHEMA IF NOT EXISTS ml
COMMENT 'ML models and artifacts';

-- Set up external locations (adjust paths for your environment)
CREATE EXTERNAL LOCATION IF NOT EXISTS bronze_storage
URL 's3://databricks-lakehouse/data/bronze/'
WITH (STORAGE CREDENTIAL aws_credential);

CREATE EXTERNAL LOCATION IF NOT EXISTS silver_storage
URL 's3://databricks-lakehouse/data/silver/'
WITH (STORAGE CREDENTIAL aws_credential);

CREATE EXTERNAL LOCATION IF NOT EXISTS gold_storage
URL 's3://databricks-lakehouse/data/gold/'
WITH (STORAGE CREDENTIAL aws_credential);

-- Enable data lineage tracking
ALTER CATALOG lakehouse SET PROPERTIES ('enable_lineage' = 'true');

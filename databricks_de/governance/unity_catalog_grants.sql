-- Unity Catalog permissions and grants for retail data lakehouse
-- Run this script to set up governance and access control

-- ============================================================================
-- CATALOG-LEVEL PERMISSIONS
-- ============================================================================

-- Grant usage on catalog to data engineering team
GRANT USE CATALOG ON CATALOG retail_datalake TO `data-engineering-team`;

-- Grant create schema to data engineering team
GRANT CREATE SCHEMA ON CATALOG retail_datalake TO `data-engineering-team`;

-- ============================================================================
-- SCHEMA-LEVEL PERMISSIONS (BRONZE)
-- ============================================================================

-- Grant usage on Bronze schema
GRANT USE SCHEMA ON SCHEMA retail_datalake.dev_bronze TO `data-engineering-team`;
GRANT USE SCHEMA ON SCHEMA retail_datalake.qa_bronze TO `data-engineering-team`;
GRANT USE SCHEMA ON SCHEMA retail_datalake.prod_bronze TO `data-engineering-team`;

-- Grant read access to Bronze for data engineers
GRANT SELECT ON SCHEMA retail_datalake.dev_bronze TO `data-engineering-team`;
GRANT SELECT ON SCHEMA retail_datalake.qa_bronze TO `data-engineering-team`;
GRANT SELECT ON SCHEMA retail_datalake.prod_bronze TO `data-engineering-team`;

-- Grant write access to Bronze for ingestion jobs
GRANT MODIFY ON SCHEMA retail_datalake.dev_bronze TO `ingestion-jobs`;
GRANT MODIFY ON SCHEMA retail_datalake.qa_bronze TO `ingestion-jobs`;
GRANT MODIFY ON SCHEMA retail_datalake.prod_bronze TO `ingestion-jobs`;

-- ============================================================================
-- SCHEMA-LEVEL PERMISSIONS (SILVER)
-- ============================================================================

-- Grant usage on Silver schema
GRANT USE SCHEMA ON SCHEMA retail_datalake.dev_silver TO `data-engineering-team`;
GRANT USE SCHEMA ON SCHEMA retail_datalake.qa_silver TO `data-engineering-team`;
GRANT USE SCHEMA ON SCHEMA retail_datalake.prod_silver TO `data-engineering-team`;

-- Grant read access to Silver
GRANT SELECT ON SCHEMA retail_datalake.dev_silver TO `data-engineering-team`;
GRANT SELECT ON SCHEMA retail_datalake.qa_silver TO `data-engineering-team`;
GRANT SELECT ON SCHEMA retail_datalake.prod_silver TO `data-engineering-team`;

-- Grant write access to Silver for transformation jobs
GRANT MODIFY ON SCHEMA retail_datalake.dev_silver TO `transformation-jobs`;
GRANT MODIFY ON SCHEMA retail_datalake.qa_silver TO `transformation-jobs`;
GRANT MODIFY ON SCHEMA retail_datalake.prod_silver TO `transformation-jobs`;

-- ============================================================================
-- SCHEMA-LEVEL PERMISSIONS (GOLD)
-- ============================================================================

-- Grant usage on Gold schema to analytics team
GRANT USE SCHEMA ON SCHEMA retail_datalake.dev_gold TO `analytics-team`;
GRANT USE SCHEMA ON SCHEMA retail_datalake.qa_gold TO `analytics-team`;
GRANT USE SCHEMA ON SCHEMA retail_datalake.prod_gold TO `analytics-team`;

-- Grant read access to Gold for BI tools and analysts
GRANT SELECT ON SCHEMA retail_datalake.dev_gold TO `analytics-team`;
GRANT SELECT ON SCHEMA retail_datalake.qa_gold TO `analytics-team`;
GRANT SELECT ON SCHEMA retail_datalake.prod_gold TO `analytics-team`;

-- Grant read access to Gold for BI tools (service principal)
GRANT SELECT ON SCHEMA retail_datalake.dev_gold TO `bi-tools-service-principal`;
GRANT SELECT ON SCHEMA retail_datalake.qa_gold TO `bi-tools-service-principal`;
GRANT SELECT ON SCHEMA retail_datalake.prod_gold TO `bi-tools-service-principal`;

-- Grant write access to Gold for transformation jobs
GRANT MODIFY ON SCHEMA retail_datalake.dev_gold TO `transformation-jobs`;
GRANT MODIFY ON SCHEMA retail_datalake.qa_gold TO `transformation-jobs`;
GRANT MODIFY ON SCHEMA retail_datalake.prod_gold TO `transformation-jobs`;

-- ============================================================================
-- TABLE-LEVEL PERMISSIONS (GOLD - FACT AND DIMENSION TABLES)
-- ============================================================================

-- Grant SELECT on fact tables
GRANT SELECT ON TABLE retail_datalake.prod_gold.fact_sales TO `analytics-team`;
GRANT SELECT ON TABLE retail_datalake.prod_gold.fact_sales TO `bi-tools-service-principal`;

-- Grant SELECT on dimension tables
GRANT SELECT ON TABLE retail_datalake.prod_gold.dim_customer TO `analytics-team`;
GRANT SELECT ON TABLE retail_datalake.prod_gold.dim_product TO `analytics-team`;
GRANT SELECT ON TABLE retail_datalake.prod_gold.dim_store TO `analytics-team`;
GRANT SELECT ON TABLE retail_datalake.prod_gold.dim_date TO `analytics-team`;

GRANT SELECT ON TABLE retail_datalake.prod_gold.dim_customer TO `bi-tools-service-principal`;
GRANT SELECT ON TABLE retail_datalake.prod_gold.dim_product TO `bi-tools-service-principal`;
GRANT SELECT ON TABLE retail_datalake.prod_gold.dim_store TO `bi-tools-service-principal`;
GRANT SELECT ON TABLE retail_datalake.prod_gold.dim_date TO `bi-tools-service-principal`;

-- ============================================================================
-- ROW-LEVEL SECURITY (EXAMPLE: Customer data filtering)
-- ============================================================================

-- Create row-level security function (if needed)
-- Example: Filter customer data based on region
-- CREATE FUNCTION retail_datalake.prod_gold.filter_customer_region(region STRING)
-- RETURNS TABLE AS
-- SELECT * FROM retail_datalake.prod_gold.dim_customer
-- WHERE customer_region = region;

-- ============================================================================
-- COLUMN-LEVEL SECURITY (EXAMPLE: Mask PII)
-- ============================================================================

-- Grant SELECT with column-level permissions (masking sensitive columns)
-- GRANT SELECT (
--   customer_key, first_name, last_name, 
--   city, state, country
-- ) ON TABLE retail_datalake.prod_gold.dim_customer 
-- TO `external-analysts`;

-- Deny access to sensitive columns
-- DENY SELECT (
--   email, phone, address, zip_code, date_of_birth
-- ) ON TABLE retail_datalake.prod_gold.dim_customer 
-- TO `external-analysts`;

-- ============================================================================
-- DELTA SHARING (Share Gold tables with external partners)
-- ============================================================================

-- Create Delta Share
-- CREATE SHARE retail_gold_share;

-- Add Gold tables to share
-- ALTER SHARE retail_gold_share ADD TABLE retail_datalake.prod_gold.fact_sales;
-- ALTER SHARE retail_gold_share ADD TABLE retail_datalake.prod_gold.dim_product;
-- ALTER SHARE retail_gold_share ADD TABLE retail_datalake.prod_gold.dim_store;

-- Grant access to share recipient
-- GRANT SELECT ON SHARE retail_gold_share TO `external-partner-recipient`;

-- ============================================================================
-- DATA LINEAGE AND METADATA
-- ============================================================================

-- Unity Catalog automatically tracks lineage for:
-- - Table-to-table dependencies
-- - Notebook-to-table lineage
-- - Query lineage
-- - Delta Sharing lineage

-- Query lineage (example)
-- SELECT * FROM system.information_schema.table_lineage
-- WHERE source_table_name = 'fact_sales';

-- ============================================================================
-- AUDIT LOGGING
-- ============================================================================

-- Unity Catalog audit logs are automatically enabled
-- Query audit logs (requires account admin access)
-- SELECT * FROM system.access.audit_log
-- WHERE service_name = 'unityCatalog'
-- AND timestamp > current_timestamp() - INTERVAL 7 DAY;


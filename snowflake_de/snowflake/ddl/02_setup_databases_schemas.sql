-- ============================================================================
-- Database and Schema Setup
-- Creates databases and schemas for each environment (Dev/QA/Prod)
-- ============================================================================

-- ============================================================================
-- DEVELOPMENT ENVIRONMENT
-- ============================================================================

-- Raw landing database (Bronze layer)
CREATE DATABASE IF NOT EXISTS DEV_RAW;
USE DATABASE DEV_RAW;

CREATE SCHEMA IF NOT EXISTS BRONZE;
CREATE SCHEMA IF NOT EXISTS METADATA;

-- Staging database (Silver layer)
CREATE DATABASE IF NOT EXISTS DEV_STAGING;
USE DATABASE DEV_STAGING;

CREATE SCHEMA IF NOT EXISTS SILVER;
CREATE SCHEMA IF NOT EXISTS STREAMS;
CREATE SCHEMA IF NOT EXISTS TASKS;

-- Data warehouse database (Gold layer)
CREATE DATABASE IF NOT EXISTS DEV_DW;
USE DATABASE DEV_DW;

CREATE SCHEMA IF NOT EXISTS DIMENSIONS;
CREATE SCHEMA IF NOT EXISTS FACTS;
CREATE SCHEMA IF NOT EXISTS MART;

-- ============================================================================
-- QA ENVIRONMENT
-- ============================================================================

-- Raw landing database (Bronze layer)
CREATE DATABASE IF NOT EXISTS QA_RAW;
USE DATABASE QA_RAW;

CREATE SCHEMA IF NOT EXISTS BRONZE;
CREATE SCHEMA IF NOT EXISTS METADATA;

-- Staging database (Silver layer)
CREATE DATABASE IF NOT EXISTS QA_STAGING;
USE DATABASE QA_STAGING;

CREATE SCHEMA IF NOT EXISTS SILVER;
CREATE SCHEMA IF NOT EXISTS STREAMS;
CREATE SCHEMA IF NOT EXISTS TASKS;

-- Data warehouse database (Gold layer)
CREATE DATABASE IF NOT EXISTS QA_DW;
USE DATABASE QA_DW;

CREATE SCHEMA IF NOT EXISTS DIMENSIONS;
CREATE SCHEMA IF NOT EXISTS FACTS;
CREATE SCHEMA IF NOT EXISTS MART;

-- ============================================================================
-- PRODUCTION ENVIRONMENT
-- ============================================================================

-- Raw landing database (Bronze layer)
CREATE DATABASE IF NOT EXISTS PROD_RAW;
USE DATABASE PROD_RAW;

CREATE SCHEMA IF NOT EXISTS BRONZE;
CREATE SCHEMA IF NOT EXISTS METADATA;

-- Staging database (Silver layer)
CREATE DATABASE IF NOT EXISTS PROD_STAGING;
USE DATABASE PROD_STAGING;

CREATE SCHEMA IF NOT EXISTS SILVER;
CREATE SCHEMA IF NOT EXISTS STREAMS;
CREATE SCHEMA IF NOT EXISTS TASKS;

-- Data warehouse database (Gold layer)
CREATE DATABASE IF NOT EXISTS PROD_DW;
USE DATABASE PROD_DW;

CREATE SCHEMA IF NOT EXISTS DIMENSIONS;
CREATE SCHEMA IF NOT EXISTS FACTS;
CREATE SCHEMA IF NOT EXISTS MART;

-- ============================================================================
-- UTILITY DATABASE (Shared across environments)
-- ============================================================================

CREATE DATABASE IF NOT EXISTS UTILITY;
USE DATABASE UTILITY;

CREATE SCHEMA IF NOT EXISTS CONFIG;
CREATE SCHEMA IF NOT EXISTS MONITORING;
CREATE SCHEMA IF NOT EXISTS AUDIT;


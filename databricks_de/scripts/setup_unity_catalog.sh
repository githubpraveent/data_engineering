#!/bin/bash

# Setup Unity Catalog for retail data lakehouse
# This script initializes Unity Catalog schemas and permissions

set -e

ENVIRONMENT=${1:-dev}

if [[ ! "$ENVIRONMENT" =~ ^(dev|qa|prod)$ ]]; then
    echo "Error: Environment must be dev, qa, or prod"
    exit 1
fi

echo "Setting up Unity Catalog for $ENVIRONMENT environment..."

# Check if databricks CLI is installed
if ! command -v databricks &> /dev/null; then
    echo "Error: Databricks CLI is not installed"
    exit 1
fi

# Run Unity Catalog SQL script
echo "Applying Unity Catalog grants..."

databricks sql execute \
    --cluster-id ${DATABRICKS_CLUSTER_ID} \
    --file governance/unity_catalog_grants.sql

echo "Unity Catalog setup completed!"

# Verify schemas exist
echo "Verifying schemas..."
databricks sql execute \
    --cluster-id ${DATABRICKS_CLUSTER_ID} \
    --query "SHOW SCHEMAS IN retail_datalake LIKE '${ENVIRONMENT}_*'"

echo "Unity Catalog verification completed!"


#!/bin/bash

# Deploy Databricks notebooks to specified environment
# Usage: ./deploy_notebooks.sh [dev|qa|prod]

set -e

ENVIRONMENT=${1:-dev}

if [[ ! "$ENVIRONMENT" =~ ^(dev|qa|prod)$ ]]; then
    echo "Error: Environment must be dev, qa, or prod"
    exit 1
fi

echo "Deploying notebooks to $ENVIRONMENT environment..."

# Set Databricks configuration based on environment
if [ "$ENVIRONMENT" == "dev" ]; then
    DATABRICKS_WORKSPACE=${DATABRICKS_DEV_WORKSPACE:-"https://dev-workspace.cloud.databricks.com"}
    TARGET_PATH="/Shared/retail-datalake/$ENVIRONMENT"
elif [ "$ENVIRONMENT" == "qa" ]; then
    DATABRICKS_WORKSPACE=${DATABRICKS_QA_WORKSPACE:-"https://qa-workspace.cloud.databricks.com"}
    TARGET_PATH="/Shared/retail-datalake/$ENVIRONMENT"
elif [ "$ENVIRONMENT" == "prod" ]; then
    DATABRICKS_WORKSPACE=${DATABRICKS_PROD_WORKSPACE:-"https://prod-workspace.cloud.databricks.com"}
    TARGET_PATH="/Shared/retail-datalake/$ENVIRONMENT"
fi

# Check if databricks CLI is installed
if ! command -v databricks &> /dev/null; then
    echo "Error: Databricks CLI is not installed"
    exit 1
fi

# Configure Databricks CLI (if not already configured)
# databricks configure --token

# Deploy notebooks
echo "Deploying notebooks from databricks/notebooks to $TARGET_PATH..."

databricks workspace import_dir \
    databricks/notebooks \
    $TARGET_PATH \
    --overwrite \
    --exclude-hidden-files

# Deploy utilities
echo "Deploying utilities..."

databricks workspace import_dir \
    databricks/notebooks/utilities \
    $TARGET_PATH/utilities \
    --overwrite

echo "Deployment completed successfully!"

# List deployed notebooks
echo "Deployed notebooks:"
databricks workspace ls $TARGET_PATH


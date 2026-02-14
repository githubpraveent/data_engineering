#!/bin/bash

# ============================================================================
# Dagster Setup Script
# Sets up Dagster for the retail data pipeline
# ============================================================================

set -e

echo "Setting up Dagster for Retail Data Pipeline..."

# Check Python version
echo "Checking Python version..."
python3 --version

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Install Dagster dependencies
echo "Installing Dagster dependencies..."
pip install --upgrade pip
pip install dagster==1.5.0 dagster-snowflake==0.21.0 dagster-webserver==1.5.0

# Create Dagster storage directory
echo "Creating Dagster storage directory..."
mkdir -p /tmp/dagster-storage

# Set environment variables
echo "Setting up environment variables..."
export DAGSTER_HOME=$(pwd)
export ENVIRONMENT=${ENVIRONMENT:-DEV}

# Initialize Dagster (if needed)
echo "Dagster setup complete!"
echo ""
echo "Next steps:"
echo "1. Set environment variables:"
echo "   export SNOWFLAKE_ACCOUNT=your_account"
echo "   export SNOWFLAKE_USER=your_user"
echo "   export SNOWFLAKE_PASSWORD=your_password"
echo "   export SNOWFLAKE_WAREHOUSE=WH_TRANS"
echo "   export SNOWFLAKE_DATABASE=${ENVIRONMENT}_RAW"
echo ""
echo "2. Start Dagster webserver:"
echo "   dagster dev -f dagster/definitions.py"
echo ""
echo "3. Or use Dagster Cloud/Dagster UI for production deployment"


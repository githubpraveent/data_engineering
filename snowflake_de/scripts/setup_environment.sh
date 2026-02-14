#!/bin/bash

# ============================================================================
# Environment Setup Script
# Sets up the development environment for the retail data pipeline
# ============================================================================

set -e

echo "Setting up Retail Data Pipeline Environment..."

# Check Python version
echo "Checking Python version..."
python3 --version

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r airflow/config/requirements.txt

# Install development dependencies
echo "Installing development dependencies..."
pip install flake8 black isort pytest pytest-cov sqlfluff

# Create necessary directories
echo "Creating directories..."
mkdir -p logs
mkdir -p tests/unit
mkdir -p tests/integration

# Set up Airflow (if not already set up)
if [ ! -f "airflow.cfg" ]; then
    echo "Initializing Airflow..."
    export AIRFLOW_HOME=$(pwd)
    airflow db init
    echo "Airflow initialized. Please configure airflow.cfg with your settings."
fi

# Create .env file template if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env template..."
    cat > .env << EOF
# Environment Configuration
ENVIRONMENT=DEV

# Snowflake Configuration
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=WH_TRANS
SNOWFLAKE_DATABASE=DEV_RAW
SNOWFLAKE_SCHEMA=BRONZE

# Airflow Configuration
AIRFLOW_HOME=$(pwd)
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__CORE__DAGS_FOLDER=$(pwd)/airflow/dags
EOF
    echo ".env file created. Please update with your actual values."
fi

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env file with your Snowflake credentials"
echo "2. Configure Airflow connections: airflow connections add snowflake_default --conn-type snowflake --conn-login <user> --conn-password <password> --conn-extra '{\"account\": \"<account>\", \"warehouse\": \"WH_TRANS\", \"database\": \"DEV_RAW\"}'"
echo "3. Run Snowflake DDL scripts to set up databases and schemas"
echo "4. Start Airflow: airflow webserver --port 8080 & airflow scheduler"


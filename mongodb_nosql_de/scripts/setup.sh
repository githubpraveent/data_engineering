#!/bin/bash
# Setup script for MongoDB Data Engineering Pipeline

set -e

echo "=== MongoDB Data Engineering Pipeline Setup ==="

# Check prerequisites
echo "Checking prerequisites..."

command -v terraform >/dev/null 2>&1 || { echo "Terraform is required but not installed. Aborting." >&2; exit 1; }
command -v ansible >/dev/null 2>&1 || { echo "Ansible is required but not installed. Aborting." >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required but not installed. Aborting." >&2; exit 1; }

echo "✓ Prerequisites check passed"

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✓ Python dependencies installed"

# Create necessary directories
echo "Creating project directories..."
mkdir -p data/source
mkdir -p logs
mkdir -p .terraform

echo "✓ Directories created"

# Initialize Terraform (optional)
read -p "Initialize Terraform? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "Initializing Terraform..."
    cd terraform/environments/staging
    terraform init -backend=false
    cd ../../..
    echo "✓ Terraform initialized"
fi

# Setup local MongoDB (optional)
read -p "Do you have MongoDB running locally? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Note: You can use MongoDB Atlas or install MongoDB locally"
    echo "For local MongoDB:"
    echo "  - macOS: brew install mongodb-community"
    echo "  - Linux: sudo apt-get install mongodb"
    echo "  - Docker: docker run -d -p 27017:27017 mongo:6.0"
fi

# Create .env file template
if [ ! -f .env ]; then
    echo "Creating .env template..."
    cat > .env << EOF
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/data_pipeline
MONGODB_DATABASE=data_pipeline

# Environment
ENVIRONMENT=development

# Source Configuration
SOURCE_TYPE=csv
SOURCE_PATH=data/sample/transactions_sample.csv

# Pipeline Configuration
PIPELINE_BATCH_SIZE=1000
PIPELINE_WORKERS=2

# Data Quality
DQ_ENABLED=true
DQ_STRICT_MODE=false
DQ_COMPLETENESS_THRESHOLD=0.95
DQ_ACCURACY_THRESHOLD=0.90
DQ_UNIQUENESS_THRESHOLD=0.99

# Logging
LOG_LEVEL=INFO
EOF
    echo "✓ .env file created (please update with your settings)"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Update .env file with your MongoDB connection string"
echo "2. Copy sample data: cp data/sample/transactions_sample.csv data/source/"
echo "3. Activate virtual environment: source venv/bin/activate"
echo "4. Run pipeline: python src/pipeline/main.py"
echo "5. Run tests: pytest tests/"
echo ""
echo "For production deployment, see docs/DEPLOYMENT.md"

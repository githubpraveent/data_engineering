# Usage Guide

## Quick Start

### Local Development

1. **Setup Environment**
   ```bash
   ./scripts/setup.sh
   source venv/bin/activate
   ```

2. **Configure Environment**
   ```bash
   # Edit .env file with your MongoDB URI
   export MONGODB_URI="mongodb://localhost:27017/data_pipeline"
   ```

3. **Run Pipeline**
   ```bash
   python src/pipeline/main.py
   ```

### Running Tests

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests (requires MongoDB)
pytest tests/integration/ -v

# Data quality tests
pytest tests/quality/ -v

# All tests with coverage
pytest tests/ --cov=src --cov-report=html
```

## Pipeline Execution

### Basic Usage

```bash
python src/pipeline/main.py
```

### With Custom Configuration

```bash
export MONGODB_URI="mongodb+srv://user:pass@cluster.mongodb.net/db"
export SOURCE_PATH="/path/to/data.csv"
export ENVIRONMENT="production"
python src/pipeline/main.py
```

### Using Configuration File

```bash
export CONFIG_PATH="/path/to/config.yml"
python src/pipeline/main.py
```

## Query Examples

### Using Python

```python
from queries.examples import QueryExamples

# Initialize
queries = QueryExamples("mongodb://localhost:27017", "data_pipeline")

# Get recent transactions
recent = queries.get_recent_transactions(limit=10)

# Top products by revenue
top_products = queries.get_top_products_by_revenue(limit=5)

# Revenue by category
categories = queries.get_revenue_by_category()

# Daily trends
trends = queries.get_daily_revenue_trends(days=30)

queries.close()
```

### Using MongoDB Shell

```javascript
// Connect to database
use data_pipeline

// Get recent transactions
db.transactions_fact.find().sort({timestamp: -1}).limit(10)

// Top products by revenue
db.transactions_fact.aggregate([
  {
    $group: {
      _id: "$product_id",
      total_revenue: {$sum: "$total_amount"},
      count: {$sum: 1}
    }
  },
  {$sort: {total_revenue: -1}},
  {$limit: 10}
])

// Revenue by region
db.transactions_fact.aggregate([
  {
    $group: {
      _id: "$region",
      total_revenue: {$sum: "$total_amount"},
      avg_transaction: {$avg: "$total_amount"}
    }
  },
  {$sort: {total_revenue: -1}}
])
```

## API Usage

### Start API Server

```bash
export MONGODB_URI="mongodb://localhost:27017"
export API_PORT=5000
python src/queries/api.py
```

### API Endpoints

#### Health Check
```bash
curl http://localhost:5000/health
```

#### Recent Transactions
```bash
curl "http://localhost:5000/api/transactions/recent?limit=10"
```

#### Search Transactions
```bash
curl "http://localhost:5000/api/transactions/search?q=PROD001&field=product_id"
```

#### Top Products
```bash
curl "http://localhost:5000/api/products/top?limit=5"
```

#### Revenue by Category
```bash
curl "http://localhost:5000/api/categories/revenue"
```

#### Daily Trends
```bash
curl "http://localhost:5000/api/trends/daily?days=30"
```

#### Paginated Transactions
```bash
curl "http://localhost:5000/api/transactions/paginated?page=1&page_size=20"
```

## Data Quality Checks

### Viewing Quality Reports

Quality validation results are logged during pipeline execution. Check logs:

```bash
tail -f /var/log/pipeline/pipeline.log | grep -i quality
```

### Configuring Quality Thresholds

Edit configuration or environment variables:

```yaml
data_quality:
  enabled: true
  strict_mode: false
  thresholds:
    completeness: 0.95
    accuracy: 0.90
    uniqueness: 0.99
```

## Monitoring

### CloudWatch Dashboard

Access the dashboard via AWS Console or use the URL from Terraform output:

```bash
terraform output cloudwatch_dashboard_url
```

### View Logs

```bash
# Local logs
tail -f /var/log/pipeline/pipeline.log

# CloudWatch logs (AWS CLI)
aws logs tail /aws/mongodb-pipeline/staging/pipeline --follow
```

### Metrics

Pipeline emits custom metrics to CloudWatch:
- `records_processed`: Number of records processed
- `records_failed`: Number of failed records
- `data_quality_score`: Data quality score (0-1)

## Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**
   - Check connection string format
   - Verify network connectivity
   - Check IP whitelist (MongoDB Atlas)

2. **Data Quality Failures**
   - Review quality logs
   - Adjust thresholds if needed
   - Check source data format

3. **Pipeline Performance Issues**
   - Increase batch size
   - Optimize indexes
   - Check network latency

4. **Import Errors**
   - Verify Python dependencies: `pip install -r requirements.txt`
   - Check Python version: `python --version` (should be 3.9+)

## Best Practices

1. **Data Sources**
   - Validate source data format before processing
   - Use idempotent operations (upsert)
   - Handle missing/null values gracefully

2. **Performance**
   - Use appropriate batch sizes
   - Create indexes on frequently queried fields
   - Monitor query performance

3. **Error Handling**
   - Enable strict mode in production for critical data
   - Log all validation failures
   - Set up alerts for quality degradation

4. **Security**
   - Use environment variables for secrets
   - Rotate credentials regularly
   - Enable MongoDB authentication
   - Use VPC peering for production

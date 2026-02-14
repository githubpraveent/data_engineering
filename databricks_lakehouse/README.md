# Databricks Lakehouse - Real-Time Customer Behavior Analytics

A complete end-to-end Databricks Lakehouse implementation featuring real-time streaming, medallion architecture, AI/ML inference, and comprehensive governance.

## 🏗️ Project Structure

```
.
├── ARCHITECTURE.md              # Architecture documentation
├── README.md                    # This file
├── config/                      # Configuration files
│   ├── workspace_config.json    # Databricks workspace settings
│   ├── kafka_config.json        # Kafka connection settings
│   └── unity_catalog_config.sql # Unity Catalog setup
├── infrastructure/              # Infrastructure as Code
│   ├── terraform/               # Terraform configurations
│   └── databricks_cluster.json  # Cluster configuration
├── notebooks/                   # Databricks notebooks
│   ├── 01_bronze_ingestion.py   # Streaming ingestion
│   ├── 02_silver_transformation.py # Data cleaning & enrichment
│   ├── 03_gold_aggregation.py   # Analytics aggregations
│   ├── 04_ml_training.py        # ML model training
│   ├── 05_ml_inference.py       # Real-time inference
│   ├── 06_governance_setup.py   # Unity Catalog setup
│   ├── 07_monitoring.py         # Monitoring & alerting
│   ├── 08_bi_queries.py         # BI queries & dashboards
│   └── 09_performance_optimization.py # Performance optimization
├── workflows/                   # Orchestration
│   ├── dlt_pipeline.py          # Delta Live Tables pipeline
│   ├── workflow_definition.json # Workflow configuration
│   └── optimization_schedule.json # Performance optimization schedule
├── tests/                       # Test cases
│   ├── test_bronze.py
│   ├── test_silver.py
│   └── test_gold.py
└── utils/                       # Utility functions
    ├── data_quality.py          # Data quality checks
    ├── monitoring_utils.py      # Monitoring helpers
    └── performance_optimizer.py # Performance optimization utilities
```

## 📈 Performance Optimization

See [PERFORMANCE_OPTIMIZATION.md](PERFORMANCE_OPTIMIZATION.md) for comprehensive performance tuning guide.

**Key Optimizations:**
- ✅ Delta Lake auto-optimize enabled
- ✅ Z-ordering for multi-column queries
- ✅ Bloom filters for fast lookups
- ✅ Adaptive Query Execution (AQE)
- ✅ Delta cache for frequently accessed data
- ✅ Automated optimization schedules

## 🚀 Quick Start

### Prerequisites

- Databricks workspace with Unity Catalog enabled
- Access to Kafka/Event Hubs/Kinesis
- Databricks CLI configured
- Python 3.8+ (for local development)

### Setup Steps

1. **Configure Unity Catalog**
   ```bash
   databricks workspace import config/unity_catalog_config.sql
   ```

2. **Deploy Infrastructure**
   ```bash
   cd infrastructure/terraform
   terraform init
   terraform plan
   terraform apply
   ```

3. **Import Notebooks**
   ```bash
   databricks workspace import_dir notebooks/ /Shared/lakehouse/
   ```

4. **Configure Streaming Source**
   - Update `config/kafka_config.json` with your Kafka broker details
   - Set up authentication credentials in Databricks secrets

5. **Run Initial Setup**
   - Execute `06_governance_setup.py` to create catalogs and schemas
   - Run `04_ml_training.py` to train the initial model

6. **Start Streaming Pipeline**
   - Deploy `workflows/dlt_pipeline.py` as a Delta Live Table
   - Or schedule notebooks as Databricks Jobs

## 📊 Use Case: Customer Behavior Analytics

### Data Schema

**Bronze (Raw Events)**
- `event_id`: Unique event identifier
- `customer_id`: Customer identifier
- `event_type`: click, purchase, review, page_view
- `timestamp`: Event timestamp
- `raw_data`: JSON payload with event details

**Silver (Cleaned)**
- All Bronze fields + enriched data
- `product_id`: Product identifier (enriched)
- `category`: Product category
- `customer_segment`: Customer segment
- `text_content`: Review text (for sentiment)
- `is_valid`: Data quality flag

**Gold (Analytics)**
- `customer_id`, `date`
- `total_events`, `total_purchases`, `total_revenue`
- `avg_sentiment_score`: Average sentiment from reviews
- `behavior_features`: ML-ready feature vector

### ML Model: Sentiment Classification

- **Input**: Review text from customer events
- **Output**: Sentiment score (positive/negative/neutral)
- **Training Data**: Gold aggregated customer reviews
- **Inference**: Real-time scoring via `ai_query` or Model Serving

## 🔐 Governance

All tables are registered in Unity Catalog with:
- **Catalogs**: `lakehouse` (production), `lakehouse_dev` (development)
- **Schemas**: `bronze`, `silver`, `gold`
- **Access Control**: Role-based permissions
- **Lineage**: Automatic tracking via Unity Catalog

## 📈 Monitoring

Key metrics tracked:
- Streaming lag (Bronze ingestion)
- Data quality scores (Silver validation)
- ML model performance (accuracy, latency)
- Processing throughput
- Error rates and failures

## 📈 Performance Optimization

See [PERFORMANCE_OPTIMIZATION.md](PERFORMANCE_OPTIMIZATION.md) for comprehensive performance tuning guide.

**Key Optimizations:**
- ✅ Delta Lake auto-optimize enabled
- ✅ Z-ordering for multi-column queries
- ✅ Bloom filters for fast lookups
- ✅ Adaptive Query Execution (AQE)
- ✅ Delta cache for frequently accessed data
- ✅ Automated optimization schedules

## 🧪 Testing

Run test suite:
```bash
pytest tests/ -v
```

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📧 Support

For issues and questions, please open a GitHub issue.

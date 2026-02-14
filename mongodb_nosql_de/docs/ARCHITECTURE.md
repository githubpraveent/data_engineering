# Architecture Documentation

## System Architecture

### High-Level Overview

The MongoDB Data Engineering Pipeline is designed as a cloud-native, scalable ETL system with the following components:

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Repository                         │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │    Code    │  │  Terraform │  │  Ansible   │           │
│  │  (Python)  │  │   (IaC)    │  │  (Config)  │           │
│  └────────────┘  └────────────┘  └────────────┘           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  GitHub Actions CI/CD                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Validate │→ │  Plan    │→ │  Apply   │→ │  Deploy  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    AWS Infrastructure                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │     VPC      │  │     EC2      │  │  CloudWatch  │     │
│  │  (Networking)│  │  (Compute)   │  │  (Monitoring)│     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  MongoDB Atlas Cluster                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │    Facts     │  │  Dimensions  │  │  Aggregates  │     │
│  │ (Transactions)│  │  (Products)  │  │ (Daily Stats)│     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Infrastructure Layer (Terraform)

**Modules:**
- **VPC**: Virtual Private Cloud with public/private subnets
- **Compute**: EC2 instances for pipeline execution
- **MongoDB**: MongoDB Atlas cluster provisioning
- **Monitoring**: CloudWatch dashboards and alarms

**Key Features:**
- Multi-AZ deployment for high availability
- Security groups for network isolation
- IAM roles for secure access
- Automated backup configuration

### 2. Configuration Layer (Ansible)

**Roles:**
- **python**: Python runtime installation
- **mongodb-client**: MongoDB tools and drivers
- **pipeline-agent**: Service configuration and deployment

**Features:**
- Idempotent configuration
- Environment-specific settings
- Automated service deployment
- Log rotation and monitoring setup

### 3. Data Pipeline Layer (Python)

**Components:**

#### Extract Module
- CSV file extraction
- JSON file extraction
- API endpoint extraction
- Error handling and logging

#### Transform Module
- Data normalization
- Schema transformation
- Timestamp parsing
- Numeric value standardization
- Aggregate collection building

#### Quality Module
- Schema validation
- Completeness checks
- Accuracy validation
- Uniqueness verification
- Quality score calculation

#### Load Module
- Batch upsert operations
- Index creation
- Connection pooling
- Error handling and retry logic

### 4. Data Storage (MongoDB)

**Collections:**

#### Facts Collection (`transactions_fact`)
- Transaction-level data
- Denormalized structure for query performance
- Indexes on common query fields
- TTL indexes for data retention (optional)

#### Dimensions Collection (`products_dim`)
- Product master data
- Slowly changing dimensions
- Reference data for lookups

#### Aggregates Collection (`daily_aggregates`)
- Pre-computed daily metrics
- Region and category breakdowns
- Updated via aggregation pipeline

**Indexes:**
- Primary: `transaction_id` (unique)
- Query: `timestamp`, `product_id`, `customer_id`, `region`, `category`
- Compound: `(timestamp, region)`, `(product_id, timestamp)`

### 5. Monitoring & Observability

**CloudWatch Metrics:**
- Pipeline execution metrics
- Data quality scores
- Record processing counts
- Error rates

**CloudWatch Logs:**
- Application logs
- Error traces
- Performance metrics

**Alarms:**
- High CPU usage
- Pipeline failures
- Low data quality scores

### 6. API & Query Layer

**REST API Endpoints:**
- `/api/transactions/recent`: Recent transactions
- `/api/transactions/search`: Search transactions
- `/api/products/top`: Top products by revenue
- `/api/categories/revenue`: Revenue by category
- `/api/trends/daily`: Daily revenue trends

**Query Examples:**
- Aggregation pipelines for analytics
- Paginated queries
- Filtered and sorted results
- Date range queries

## Data Flow

### ETL Process Flow

```
Source Data (CSV/API)
    │
    ▼
[Extract]
    │
    ▼
Raw Data
    │
    ▼
[Transform]
    │
    ▼
Normalized Data
    │
    ▼
[Validate]
    │
    ├─→ Passed Records
    │       │
    │       ▼
    │   [Load] → MongoDB Facts Collection
    │
    └─→ Failed Records → Logged/Alerted
            │
            ▼
        [Quality Report]
```

### Aggregate Building Process

```
Facts Collection
    │
    ▼
[Aggregation Pipeline]
    │
    ├─→ Group by Date, Region, Category
    ├─→ Calculate Metrics (Revenue, Count, Averages)
    └─→ Merge into Aggregates Collection
```

## Scalability Considerations

### Horizontal Scaling
- Multiple EC2 instances for parallel processing
- MongoDB sharding for large datasets
- Load balancing for API requests

### Vertical Scaling
- Increase instance sizes
- MongoDB cluster tier upgrades
- Batch size optimization

### Performance Optimization
- Batch processing
- Index optimization
- Connection pooling
- Caching frequently accessed data

## Security Architecture

### Network Security
- VPC isolation
- Private subnets for compute
- Security groups with least privilege
- VPC peering for MongoDB Atlas

### Access Control
- IAM roles with minimal permissions
- MongoDB user authentication
- SSH key-based access
- Secrets management via GitHub Secrets

### Data Security
- Encryption at rest (MongoDB Atlas)
- Encryption in transit (TLS)
- Secure credential storage
- Audit logging

## Disaster Recovery

### Backup Strategy
- MongoDB Atlas automated backups
- Point-in-time recovery enabled
- Terraform state in S3
- Configuration versioning in Git

### Recovery Procedures
- Infrastructure: Terraform apply from state
- Data: MongoDB Atlas backup restoration
- Application: Ansible redeployment

## Cost Optimization

### Resource Sizing
- Right-sized EC2 instances
- Appropriate MongoDB cluster tiers
- Scheduled scaling (start/stop instances)

### Monitoring Costs
- CloudWatch cost alerts
- Resource tagging for cost allocation
- Regular review of unused resources

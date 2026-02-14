# Architecture Documentation

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Retail Sources                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   POS System │  │  Order DB    │  │  Rewards DB  │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼──────────────────┘
          │                  │                  │
          │ Real-time        │ Batch/CDC        │ Batch/CDC
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼──────────────────┐
│                    INGESTION LAYER                               │
│  ┌─────────────────┐      ┌──────────────────┐                 │
│  │  Event Hubs     │      │  Data Factory    │                 │
│  │  (Streaming)    │      │  (Batch/CDC)     │                 │
│  └────────┬────────┘      └────────┬─────────┘                 │
└───────────┼─────────────────────────┼────────────────────────────┘
            │                         │
            └─────────────┬───────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                    DATA LAKE (ADLS Gen2)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Bronze/Raw  │→ │ Silver/Stage │→ │  Gold/Curated│          │
│  │  (Raw Data)  │  │  (Cleaned)   │  │  (Business)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│              TRANSFORMATION LAYER                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         Azure Databricks (Spark + Delta Lake)            │   │
│  │  • Batch ETL                                              │   │
│  │  • Streaming ETL                                          │   │
│  │  • Data Quality Checks                                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│              ORCHESTRATION LAYER                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │      Apache Airflow (on AKS)                              │   │
│  │  • Coordinate ingestion                                  │   │
│  │  • Schedule transformations                               │   │
│  │  • Manage data warehouse loads                           │   │
│  │  • Run data quality tests                                │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│              DATA WAREHOUSE (Synapse Analytics)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Dimensions  │  │  Fact Tables │  │  Staging     │          │
│  │  (SCD 1 & 2) │  │  (Incremental)│  │  Schemas     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│              GOVERNANCE & METADATA                               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         Azure Purview                                    │   │
│  │  • Data Catalog                                          │   │
│  │  • Lineage Tracking                                      │   │
│  │  • Access Governance                                     │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Ingestion Layer

#### Azure Event Hubs
- **Purpose**: Real-time event streaming from POS systems
- **Configuration**: 
  - Throughput units: Auto-scaling based on load
  - Retention: 7 days (configurable)
  - Consumer groups: Separate for different downstream consumers
- **Data Format**: JSON events (standardized schema)

#### Azure Data Factory
- **Purpose**: Batch ingestion and CDC orchestration
- **Activities**:
  - Copy data from source systems to ADLS Bronze
  - CDC extraction from source databases
  - File-based batch loads
- **Triggers**: Scheduled (daily/hourly) and event-based

### 2. Data Lake (ADLS Gen2)

#### Medallion Architecture

**Bronze/Raw Layer**
- **Location**: `adls://<storage>/bronze/`
- **Purpose**: Raw, unprocessed data as-is from sources
- **Format**: Parquet, JSON, CSV (source-dependent)
- **Retention**: 90 days (configurable)
- **Partitioning**: By source system, date, and entity type

**Silver/Staging Layer**
- **Location**: `adls://<storage>/silver/`
- **Purpose**: Cleaned, validated, and standardized data
- **Format**: Delta Lake tables
- **Transformations**:
  - Schema standardization
  - Data type conversions
  - Basic validation
  - Deduplication

**Gold/Curated Layer**
- **Location**: `adls://<storage>/gold/`
- **Purpose**: Business-ready, aggregated, and enriched data
- **Format**: Delta Lake tables
- **Transformations**:
  - Business logic application
  - Joins across sources
  - Aggregations
  - Calculated fields

#### Lifecycle Management
- **Hot Tier**: Recent data (0-30 days)
- **Cool Tier**: Older data (30-90 days)
- **Archive Tier**: Historical data (>90 days, rarely accessed)

### 3. Transformation Layer (Databricks)

#### Cluster Configuration
- **Standard Cluster**: For scheduled batch jobs
- **High Concurrency Cluster**: For interactive analysis
- **Job Clusters**: Auto-terminating for cost optimization

#### Delta Lake Features
- **ACID Transactions**: Ensures data consistency
- **Schema Evolution**: Handles schema changes gracefully
- **Time Travel**: Query historical versions of data
- **Upsert Operations**: Efficient merge operations

#### Notebook Structure
- **Ingestion Notebooks**: Stream from Event Hubs to Bronze
- **Transformation Notebooks**: Bronze → Silver → Gold
- **Quality Notebooks**: Data quality checks and validation

### 4. Orchestration (Airflow)

#### Deployment
- **Platform**: Azure Kubernetes Service (AKS)
- **Image**: Apache Airflow official image
- **Storage**: Azure Files for DAGs and logs
- **Database**: Azure Database for PostgreSQL (managed)

#### DAG Structure
```
dags/
├── ingestion/
│   ├── stream_pos_events.py
│   ├── batch_order_ingestion.py
│   └── cdc_rewards_db.py
├── transformation/
│   ├── bronze_to_silver.py
│   ├── silver_to_gold.py
│   └── data_quality_checks.py
└── warehouse/
    ├── load_dimensions.py
    ├── load_facts.py
    └── run_scd_procedures.py
```

#### Key DAG Features
- **Retry Logic**: Configurable retries with exponential backoff
- **Alerting**: Email/Slack notifications on failures
- **Monitoring**: Integration with Azure Monitor
- **Dependencies**: Proper task dependencies and scheduling

### 5. Data Warehouse (Synapse Analytics)

#### Schema Design

**Staging Schema**
- Raw data from data lake
- Temporary tables for ETL processing
- No business logic applied

**Dimension Schema**
- Customer dimension (SCD Type 2)
- Product dimension (SCD Type 1)
- Store dimension (SCD Type 2)
- Date dimension (static)
- Geography dimension (SCD Type 2)

**Fact Schema**
- Sales fact (incremental load)
- Order fact (incremental load)
- Inventory fact (snapshot)

#### SCD Implementation

**SCD Type 1** (Overwrite)
- Product dimension
- Simple attributes that don't require history

**SCD Type 2** (Historical)
- Customer dimension
- Store dimension
- Geography dimension
- Maintains effective dates and current flag

#### Performance Optimization
- **Distribution Strategy**: Hash distribution on fact table keys
- **Indexing**: Clustered columnstore indexes
- **Partitioning**: Date-based partitioning on fact tables
- **Statistics**: Auto-update statistics enabled

### 6. Governance (Purview)

#### Data Catalog
- Automatic scanning of ADLS, Synapse, Databricks
- Schema discovery and classification
- Business glossary and terms

#### Lineage
- End-to-end data lineage tracking
- From source systems to data warehouse
- Impact analysis for changes

#### Access Control
- Integration with Azure AD
- Role-based access control (RBAC)
- Data classification and sensitivity labels

## Data Flow Examples

### Real-Time Ingestion Flow
1. POS system sends event to Event Hubs
2. Databricks streaming job reads from Event Hubs
3. Data lands in ADLS Bronze (raw format)
4. Airflow triggers transformation DAG
5. Data flows through Silver → Gold layers
6. Gold data loaded to Synapse warehouse

### Batch Ingestion Flow
1. ADF pipeline triggered (scheduled or event)
2. Extract data from source (database/file)
3. Load to ADLS Bronze
4. Airflow DAG triggers Databricks transformation
5. Data quality checks run
6. Curated data loaded to Synapse

### CDC Flow
1. ADF pipeline detects changes in source
2. Extract changed records only
3. Load to ADLS Bronze (incremental)
4. Databricks merge operation updates Silver/Gold
5. Synapse dimension/fact tables updated incrementally

## Security Architecture

### Network Security
- Private endpoints for ADLS, Synapse, Databricks
- VNet integration where applicable
- Network security groups (NSGs)

### Access Control
- Azure AD authentication
- Service principals for service-to-service
- Managed identities where possible
- Key Vault for secrets management

### Data Encryption
- Encryption at rest: Azure-managed keys
- Encryption in transit: TLS 1.2+
- Customer-managed keys (CMK) option

## Monitoring & Alerting

### Azure Monitor
- Metrics collection from all services
- Log Analytics workspace
- Application Insights for Airflow

### Key Metrics
- Event Hubs: Throughput, latency, errors
- Databricks: Job success/failure, duration
- Synapse: Query performance, DWU utilization
- Airflow: DAG success/failure, task duration

### Alerting
- Failed DAG runs → Email/Slack
- High error rates → PagerDuty
- Performance degradation → Teams notification

## Scalability & Performance

### Auto-Scaling
- Event Hubs: Throughput units auto-scale
- Databricks: Cluster auto-scaling
- Synapse: Pause/resume for cost optimization

### Performance Tuning
- Databricks: Optimize Spark configurations
- Synapse: Distribution and indexing strategies
- ADLS: Optimize partition sizes

## Disaster Recovery

### Backup Strategy
- ADLS: Geo-redundant storage (GRS)
- Synapse: Automated backups (7-35 days)
- Airflow: DAGs in Git (version control)

### Recovery Procedures
- Documented RTO/RPO targets
- Automated failover for critical components
- Regular DR drills


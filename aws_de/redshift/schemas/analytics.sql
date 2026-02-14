-- Redshift Analytics Schema
-- Star schema for data warehouse

-- Date Dimension
CREATE TABLE IF NOT EXISTS analytics.dim_date (
    date_key INTEGER NOT NULL,
    date DATE NOT NULL,
    year INTEGER,
    quarter INTEGER,
    month INTEGER,
    month_name VARCHAR(20),
    week INTEGER,
    day INTEGER,
    day_name VARCHAR(20),
    is_weekend BOOLEAN,
    is_holiday BOOLEAN,
    CONSTRAINT pk_dim_date PRIMARY KEY (date_key)
)
DISTSTYLE ALL
SORTKEY (date_key);

-- Customer Dimension (SCD Type 2)
CREATE TABLE IF NOT EXISTS analytics.dim_customer (
    customer_sk INTEGER IDENTITY(1,1) NOT NULL,
    customer_id INTEGER NOT NULL,
    customer_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    effective_date DATE NOT NULL,
    end_date DATE,
    is_current BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT GETDATE(),
    updated_at TIMESTAMP DEFAULT GETDATE(),
    CONSTRAINT pk_dim_customer PRIMARY KEY (customer_sk)
)
DISTSTYLE KEY
DISTKEY (customer_id)
SORTKEY (customer_id, effective_date);

-- Product Dimension (SCD Type 1)
CREATE TABLE IF NOT EXISTS analytics.dim_product (
    product_sk INTEGER IDENTITY(1,1) NOT NULL,
    product_id INTEGER NOT NULL,
    product_name VARCHAR(255),
    category VARCHAR(100),
    price DECIMAL(10, 2),
    description TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT GETDATE(),
    CONSTRAINT pk_dim_product PRIMARY KEY (product_sk),
    CONSTRAINT uk_dim_product_product_id UNIQUE (product_id)
)
DISTSTYLE KEY
DISTKEY (product_id)
SORTKEY (product_id);

-- Sales Fact Table
CREATE TABLE IF NOT EXISTS analytics.fact_sales (
    sales_sk BIGINT IDENTITY(1,1) NOT NULL,
    order_id INTEGER NOT NULL,
    customer_sk INTEGER NOT NULL,
    product_sk INTEGER NOT NULL,
    order_date_key INTEGER NOT NULL,
    order_date TIMESTAMP NOT NULL,
    quantity INTEGER,
    unit_price DECIMAL(10, 2),
    sales_amount DECIMAL(10, 2),
    discount_amount DECIMAL(10, 2) DEFAULT 0,
    net_sales_amount DECIMAL(10, 2),
    order_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT GETDATE(),
    CONSTRAINT pk_fact_sales PRIMARY KEY (sales_sk),
    CONSTRAINT fk_fact_sales_customer FOREIGN KEY (customer_sk) REFERENCES analytics.dim_customer(customer_sk),
    CONSTRAINT fk_fact_sales_product FOREIGN KEY (product_sk) REFERENCES analytics.dim_product(product_sk),
    CONSTRAINT fk_fact_sales_date FOREIGN KEY (order_date_key) REFERENCES analytics.dim_date(date_key)
)
DISTSTYLE KEY
DISTKEY (order_id)
SORTKEY (order_date_key, order_id);

-- Sales Summary (Aggregate Table)
CREATE TABLE IF NOT EXISTS analytics.fact_sales_summary (
    summary_date_key INTEGER NOT NULL,
    customer_sk INTEGER,
    product_sk INTEGER,
    total_orders INTEGER,
    total_quantity INTEGER,
    total_sales_amount DECIMAL(12, 2),
    total_discount_amount DECIMAL(12, 2),
    total_net_sales_amount DECIMAL(12, 2),
    created_at TIMESTAMP DEFAULT GETDATE(),
    updated_at TIMESTAMP DEFAULT GETDATE(),
    CONSTRAINT pk_fact_sales_summary PRIMARY KEY (summary_date_key, customer_sk, product_sk),
    CONSTRAINT fk_fact_sales_summary_date FOREIGN KEY (summary_date_key) REFERENCES analytics.dim_date(date_key),
    CONSTRAINT fk_fact_sales_summary_customer FOREIGN KEY (customer_sk) REFERENCES analytics.dim_customer(customer_sk),
    CONSTRAINT fk_fact_sales_summary_product FOREIGN KEY (product_sk) REFERENCES analytics.dim_product(product_sk)
)
DISTSTYLE KEY
DISTKEY (summary_date_key)
SORTKEY (summary_date_key, customer_sk);

-- Grant permissions
GRANT SELECT ON analytics.dim_date TO PUBLIC;
GRANT SELECT ON analytics.dim_customer TO PUBLIC;
GRANT SELECT ON analytics.dim_product TO PUBLIC;
GRANT SELECT ON analytics.fact_sales TO PUBLIC;
GRANT SELECT ON analytics.fact_sales_summary TO PUBLIC;


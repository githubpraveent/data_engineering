-- Fact Schema for Synapse Analytics
-- Contains fact tables for analytical queries

IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'dwh')
BEGIN
    EXEC('CREATE SCHEMA dwh')
END
GO

-- Sales Fact Table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dwh].[fact_sales]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dwh].[fact_sales] (
        [sales_fact_key] BIGINT NOT NULL IDENTITY(1,1),
        [date_key] INT NOT NULL,
        [customer_key] INT NOT NULL,
        [product_key] INT NOT NULL,
        [store_key] INT NOT NULL,
        [geography_key] INT NULL,
        [transaction_id] NVARCHAR(100) NOT NULL,
        [transaction_timestamp] DATETIME2 NOT NULL,
        [quantity] INT NOT NULL,
        [unit_price] DECIMAL(10,2) NOT NULL,
        [line_total] DECIMAL(10,2) NOT NULL,
        [discount_amount] DECIMAL(10,2) NULL DEFAULT 0,
        [tax_amount] DECIMAL(10,2) NULL DEFAULT 0,
        [net_amount] DECIMAL(10,2) NOT NULL,
        [created_timestamp] DATETIME2 NOT NULL DEFAULT GETDATE(),
        CONSTRAINT [PK_fact_sales] PRIMARY KEY NONCLUSTERED ([sales_fact_key])
    )
    WITH (
        DISTRIBUTION = HASH([date_key]),
        CLUSTERED COLUMNSTORE INDEX,
        PARTITION ([date_key] RANGE RIGHT FOR VALUES (
            -- Partition by month (example values, adjust as needed)
            20200101, 20200201, 20200301, 20200401, 20200501, 20200601,
            20200701, 20200801, 20200901, 20201001, 20201101, 20201201
        ))
    )
    
    -- Create indexes for common query patterns
    CREATE NONCLUSTERED INDEX [IX_fact_sales_customer] ON [dwh].[fact_sales] ([customer_key])
    CREATE NONCLUSTERED INDEX [IX_fact_sales_product] ON [dwh].[fact_sales] ([product_key])
    CREATE NONCLUSTERED INDEX [IX_fact_sales_store] ON [dwh].[fact_sales] ([store_key])
END
GO

-- Order Fact Table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dwh].[fact_orders]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dwh].[fact_orders] (
        [order_fact_key] BIGINT NOT NULL IDENTITY(1,1),
        [date_key] INT NOT NULL,
        [customer_key] INT NOT NULL,
        [store_key] INT NOT NULL,
        [geography_key] INT NULL,
        [order_id] NVARCHAR(100) NOT NULL,
        [order_date] DATETIME2 NOT NULL,
        [order_status] NVARCHAR(50) NOT NULL,
        [total_amount] DECIMAL(10,2) NOT NULL,
        [shipping_cost] DECIMAL(10,2) NULL DEFAULT 0,
        [tax_amount] DECIMAL(10,2) NULL DEFAULT 0,
        [discount_amount] DECIMAL(10,2) NULL DEFAULT 0,
        [net_amount] DECIMAL(10,2) NOT NULL,
        [item_count] INT NOT NULL,
        [created_timestamp] DATETIME2 NOT NULL DEFAULT GETDATE(),
        CONSTRAINT [PK_fact_orders] PRIMARY KEY NONCLUSTERED ([order_fact_key])
    )
    WITH (
        DISTRIBUTION = HASH([date_key]),
        CLUSTERED COLUMNSTORE INDEX,
        PARTITION ([date_key] RANGE RIGHT FOR VALUES (
            20200101, 20200201, 20200301, 20200401, 20200501, 20200601,
            20200701, 20200801, 20200901, 20201001, 20201101, 20201201
        ))
    )
    
    CREATE NONCLUSTERED INDEX [IX_fact_orders_customer] ON [dwh].[fact_orders] ([customer_key])
    CREATE NONCLUSTERED INDEX [IX_fact_orders_store] ON [dwh].[fact_orders] ([store_key])
END
GO

-- Inventory Fact Table (Snapshot)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dwh].[fact_inventory]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dwh].[fact_inventory] (
        [inventory_fact_key] BIGINT NOT NULL IDENTITY(1,1),
        [date_key] INT NOT NULL,
        [product_key] INT NOT NULL,
        [store_key] INT NOT NULL,
        [snapshot_date] DATE NOT NULL,
        [quantity_on_hand] INT NOT NULL,
        [quantity_reserved] INT NULL DEFAULT 0,
        [quantity_available] INT NOT NULL,
        [reorder_level] INT NULL,
        [reorder_quantity] INT NULL,
        [unit_cost] DECIMAL(10,2) NULL,
        [total_value] DECIMAL(10,2) NULL,
        [created_timestamp] DATETIME2 NOT NULL DEFAULT GETDATE(),
        CONSTRAINT [PK_fact_inventory] PRIMARY KEY NONCLUSTERED ([inventory_fact_key])
    )
    WITH (
        DISTRIBUTION = HASH([date_key]),
        CLUSTERED COLUMNSTORE INDEX,
        PARTITION ([date_key] RANGE RIGHT FOR VALUES (
            20200101, 20200201, 20200301, 20200401, 20200501, 20200601,
            20200701, 20200801, 20200901, 20201001, 20201101, 20201201
        ))
    )
    
    CREATE NONCLUSTERED INDEX [IX_fact_inventory_product] ON [dwh].[fact_inventory] ([product_key])
    CREATE NONCLUSTERED INDEX [IX_fact_inventory_store] ON [dwh].[fact_inventory] ([store_key])
END
GO


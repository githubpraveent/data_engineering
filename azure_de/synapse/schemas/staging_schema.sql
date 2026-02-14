-- Staging Schema for Synapse Analytics
-- This schema holds raw data from the data lake before transformation

IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'staging')
BEGIN
    EXEC('CREATE SCHEMA staging')
END
GO

-- Staging table for POS events
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[staging].[pos_events]') AND type in (N'U'))
BEGIN
    CREATE TABLE [staging].[pos_events] (
        [event_id] NVARCHAR(100) NOT NULL,
        [store_id] NVARCHAR(50) NOT NULL,
        [transaction_id] NVARCHAR(100) NOT NULL,
        [customer_id] NVARCHAR(100) NULL,
        [product_id] NVARCHAR(100) NOT NULL,
        [quantity] INT NOT NULL,
        [price] DECIMAL(10,2) NOT NULL,
        [transaction_timestamp] DATETIME2 NOT NULL,
        [event_timestamp] DATETIME2 NULL,
        [ingestion_timestamp] DATETIME2 NOT NULL,
        [processing_date] DATE NOT NULL,
        [partition_id] INT NULL,
        [offset_id] BIGINT NULL
    )
    WITH (
        DISTRIBUTION = HASH([transaction_id]),
        CLUSTERED COLUMNSTORE INDEX
    )
END
GO

-- Staging table for orders
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[staging].[orders]') AND type in (N'U'))
BEGIN
    CREATE TABLE [staging].[orders] (
        [order_id] NVARCHAR(100) NOT NULL,
        [customer_id] NVARCHAR(100) NOT NULL,
        [store_id] NVARCHAR(50) NOT NULL,
        [order_date] DATETIME2 NOT NULL,
        [order_status] NVARCHAR(50) NOT NULL,
        [total_amount] DECIMAL(10,2) NOT NULL,
        [shipping_address] NVARCHAR(500) NULL,
        [billing_address] NVARCHAR(500) NULL,
        [ingestion_timestamp] DATETIME2 NOT NULL,
        [processing_date] DATE NOT NULL
    )
    WITH (
        DISTRIBUTION = HASH([order_id]),
        CLUSTERED COLUMNSTORE INDEX
    )
END
GO

-- Staging table for rewards
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[staging].[rewards]') AND type in (N'U'))
BEGIN
    CREATE TABLE [staging].[rewards] (
        [reward_id] NVARCHAR(100) NOT NULL,
        [customer_id] NVARCHAR(100) NOT NULL,
        [reward_points] INT NOT NULL,
        [reward_date] DATETIME2 NOT NULL,
        [expiry_date] DATETIME2 NULL,
        [reward_status] NVARCHAR(50) NOT NULL,
        [ingestion_timestamp] DATETIME2 NOT NULL,
        [processing_date] DATE NOT NULL
    )
    WITH (
        DISTRIBUTION = HASH([reward_id]),
        CLUSTERED COLUMNSTORE INDEX
    )
END
GO


-- Dimension Schema for Synapse Analytics
-- Contains dimension tables with SCD Type 1 and Type 2 support

IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'dwh')
BEGIN
    EXEC('CREATE SCHEMA dwh')
END
GO

-- Date Dimension (Static, no SCD needed)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dwh].[dim_date]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dwh].[dim_date] (
        [date_key] INT NOT NULL,
        [date] DATE NOT NULL,
        [day] INT NOT NULL,
        [month] INT NOT NULL,
        [year] INT NOT NULL,
        [quarter] INT NOT NULL,
        [week] INT NOT NULL,
        [day_of_week] INT NOT NULL,
        [day_name] NVARCHAR(10) NOT NULL,
        [month_name] NVARCHAR(10) NOT NULL,
        [is_weekend] BIT NOT NULL,
        [is_holiday] BIT NOT NULL,
        CONSTRAINT [PK_dim_date] PRIMARY KEY NONCLUSTERED ([date_key])
    )
    WITH (
        DISTRIBUTION = REPLICATE,
        CLUSTERED COLUMNSTORE INDEX
    )
END
GO

-- Customer Dimension (SCD Type 2)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dwh].[dim_customer]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dwh].[dim_customer] (
        [customer_key] INT NOT NULL IDENTITY(1,1),
        [customer_id] NVARCHAR(100) NOT NULL,
        [customer_name] NVARCHAR(200) NOT NULL,
        [email] NVARCHAR(200) NULL,
        [phone] NVARCHAR(50) NULL,
        [address] NVARCHAR(500) NULL,
        [city] NVARCHAR(100) NULL,
        [state] NVARCHAR(50) NULL,
        [zip_code] NVARCHAR(20) NULL,
        [country] NVARCHAR(50) NULL,
        [customer_segment] NVARCHAR(50) NULL,
        [effective_date] DATE NOT NULL,
        [expiry_date] DATE NULL,
        [is_current] BIT NOT NULL DEFAULT 1,
        [created_timestamp] DATETIME2 NOT NULL DEFAULT GETDATE(),
        [updated_timestamp] DATETIME2 NOT NULL DEFAULT GETDATE(),
        CONSTRAINT [PK_dim_customer] PRIMARY KEY NONCLUSTERED ([customer_key])
    )
    WITH (
        DISTRIBUTION = HASH([customer_id]),
        CLUSTERED COLUMNSTORE INDEX
    )
    
    -- Create index for current records
    CREATE CLUSTERED INDEX [IX_dim_customer_current] ON [dwh].[dim_customer] ([customer_id], [is_current])
    WHERE [is_current] = 1
END
GO

-- Product Dimension (SCD Type 1 - overwrite)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dwh].[dim_product]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dwh].[dim_product] (
        [product_key] INT NOT NULL IDENTITY(1,1),
        [product_id] NVARCHAR(100) NOT NULL,
        [product_name] NVARCHAR(200) NOT NULL,
        [product_category] NVARCHAR(100) NULL,
        [product_subcategory] NVARCHAR(100) NULL,
        [brand] NVARCHAR(100) NULL,
        [unit_price] DECIMAL(10,2) NULL,
        [cost] DECIMAL(10,2) NULL,
        [supplier_id] NVARCHAR(100) NULL,
        [created_timestamp] DATETIME2 NOT NULL DEFAULT GETDATE(),
        [updated_timestamp] DATETIME2 NOT NULL DEFAULT GETDATE(),
        CONSTRAINT [PK_dim_product] PRIMARY KEY NONCLUSTERED ([product_key])
    )
    WITH (
        DISTRIBUTION = HASH([product_id]),
        CLUSTERED COLUMNSTORE INDEX
    )
    
    CREATE UNIQUE CLUSTERED INDEX [IX_dim_product_id] ON [dwh].[dim_product] ([product_id])
END
GO

-- Store Dimension (SCD Type 2)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dwh].[dim_store]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dwh].[dim_store] (
        [store_key] INT NOT NULL IDENTITY(1,1),
        [store_id] NVARCHAR(50) NOT NULL,
        [store_name] NVARCHAR(200) NOT NULL,
        [store_type] NVARCHAR(50) NULL,
        [address] NVARCHAR(500) NULL,
        [city] NVARCHAR(100) NULL,
        [state] NVARCHAR(50) NULL,
        [zip_code] NVARCHAR(20) NULL,
        [country] NVARCHAR(50) NULL,
        [geography_key] INT NULL,
        [manager_name] NVARCHAR(200) NULL,
        [opening_date] DATE NULL,
        [effective_date] DATE NOT NULL,
        [expiry_date] DATE NULL,
        [is_current] BIT NOT NULL DEFAULT 1,
        [created_timestamp] DATETIME2 NOT NULL DEFAULT GETDATE(),
        [updated_timestamp] DATETIME2 NOT NULL DEFAULT GETDATE(),
        CONSTRAINT [PK_dim_store] PRIMARY KEY NONCLUSTERED ([store_key])
    )
    WITH (
        DISTRIBUTION = HASH([store_id]),
        CLUSTERED COLUMNSTORE INDEX
    )
    
    CREATE CLUSTERED INDEX [IX_dim_store_current] ON [dwh].[dim_store] ([store_id], [is_current])
    WHERE [is_current] = 1
END
GO

-- Geography Dimension (SCD Type 2)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dwh].[dim_geography]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dwh].[dim_geography] (
        [geography_key] INT NOT NULL IDENTITY(1,1),
        [city] NVARCHAR(100) NOT NULL,
        [state] NVARCHAR(50) NOT NULL,
        [zip_code] NVARCHAR(20) NULL,
        [country] NVARCHAR(50) NOT NULL,
        [region] NVARCHAR(50) NULL,
        [latitude] DECIMAL(10,8) NULL,
        [longitude] DECIMAL(11,8) NULL,
        [effective_date] DATE NOT NULL,
        [expiry_date] DATE NULL,
        [is_current] BIT NOT NULL DEFAULT 1,
        [created_timestamp] DATETIME2 NOT NULL DEFAULT GETDATE(),
        [updated_timestamp] DATETIME2 NOT NULL DEFAULT GETDATE(),
        CONSTRAINT [PK_dim_geography] PRIMARY KEY NONCLUSTERED ([geography_key])
    )
    WITH (
        DISTRIBUTION = REPLICATE,
        CLUSTERED COLUMNSTORE INDEX
    )
END
GO


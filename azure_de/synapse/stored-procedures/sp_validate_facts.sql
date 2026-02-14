-- Stored Procedure: Validate Fact Loads
-- This procedure performs data quality checks on fact tables

CREATE OR ALTER PROCEDURE [dwh].[sp_validate_facts]
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @ValidationResults TABLE (
        fact_table_name NVARCHAR(100),
        check_name NVARCHAR(100),
        check_result NVARCHAR(20),
        check_message NVARCHAR(500)
    );
    
    -- Validate Sales Fact
    -- Check referential integrity with dimensions
    IF EXISTS (
        SELECT * 
        FROM [dwh].[fact_sales] f
        LEFT JOIN [dwh].[dim_date] dd ON f.date_key = dd.date_key
        LEFT JOIN [dwh].[dim_customer] dc ON f.customer_key = dc.customer_key
        LEFT JOIN [dwh].[dim_product] dp ON f.product_key = dp.product_key
        LEFT JOIN [dwh].[dim_store] ds ON f.store_key = ds.store_key
        WHERE dd.date_key IS NULL
            OR dc.customer_key IS NULL
            OR dp.product_key IS NULL
            OR ds.store_key IS NULL
    )
    BEGIN
        INSERT INTO @ValidationResults
        VALUES ('fact_sales', 'Referential Integrity', 'FAILED', 'Found orphaned records in fact_sales');
    END
    ELSE
    BEGIN
        INSERT INTO @ValidationResults
        VALUES ('fact_sales', 'Referential Integrity', 'PASSED', 'All foreign keys are valid');
    END
    
    -- Check for negative amounts
    IF EXISTS (
        SELECT * 
        FROM [dwh].[fact_sales]
        WHERE net_amount < 0
    )
    BEGIN
        INSERT INTO @ValidationResults
        VALUES ('fact_sales', 'Negative Amounts', 'WARNING', 'Found negative net_amount values');
    END
    ELSE
    BEGIN
        INSERT INTO @ValidationResults
        VALUES ('fact_sales', 'Negative Amounts', 'PASSED', 'No negative amounts found');
    END
    
    -- Check for null key values
    IF EXISTS (
        SELECT * 
        FROM [dwh].[fact_sales]
        WHERE date_key IS NULL
            OR customer_key IS NULL
            OR product_key IS NULL
            OR store_key IS NULL
    )
    BEGIN
        INSERT INTO @ValidationResults
        VALUES ('fact_sales', 'Null Keys', 'FAILED', 'Found null key values in fact_sales');
    END
    ELSE
    BEGIN
        INSERT INTO @ValidationResults
        VALUES ('fact_sales', 'Null Keys', 'PASSED', 'No null keys found');
    END
    
    -- Validate Order Fact
    -- Similar checks for order fact
    IF EXISTS (
        SELECT * 
        FROM [dwh].[fact_orders] f
        LEFT JOIN [dwh].[dim_date] dd ON f.date_key = dd.date_key
        LEFT JOIN [dwh].[dim_customer] dc ON f.customer_key = dc.customer_key
        LEFT JOIN [dwh].[dim_store] ds ON f.store_key = ds.store_key
        WHERE dd.date_key IS NULL
            OR dc.customer_key IS NULL
            OR ds.store_key IS NULL
    )
    BEGIN
        INSERT INTO @ValidationResults
        VALUES ('fact_orders', 'Referential Integrity', 'FAILED', 'Found orphaned records in fact_orders');
    END
    ELSE
    BEGIN
        INSERT INTO @ValidationResults
        VALUES ('fact_orders', 'Referential Integrity', 'PASSED', 'All foreign keys are valid');
    END
    
    -- Return validation results
    SELECT * FROM @ValidationResults;
    
    -- Check if any critical validations failed
    IF EXISTS (SELECT * FROM @ValidationResults WHERE check_result = 'FAILED')
    BEGIN
        RAISERROR('Fact validation failed. Check results above.', 16, 1);
    END
    ELSE
    BEGIN
        PRINT 'All fact validations passed successfully.';
    END
END
GO


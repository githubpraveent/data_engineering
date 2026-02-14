-- Stored Procedure: Validate Dimension Loads
-- This procedure performs data quality checks on dimension tables

CREATE OR ALTER PROCEDURE [dwh].[sp_validate_dimensions]
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @ValidationResults TABLE (
        dimension_name NVARCHAR(100),
        check_name NVARCHAR(100),
        check_result NVARCHAR(20),
        check_message NVARCHAR(500)
    );
    
    -- Validate Customer Dimension
    -- Check for duplicate current records
    IF EXISTS (
        SELECT customer_id, COUNT(*) 
        FROM [dwh].[dim_customer]
        WHERE is_current = 1
        GROUP BY customer_id
        HAVING COUNT(*) > 1
    )
    BEGIN
        INSERT INTO @ValidationResults
        VALUES ('dim_customer', 'Duplicate Current Records', 'FAILED', 'Found duplicate current records for same customer_id');
    END
    ELSE
    BEGIN
        INSERT INTO @ValidationResults
        VALUES ('dim_customer', 'Duplicate Current Records', 'PASSED', 'No duplicate current records found');
    END
    
    -- Check for records with invalid date ranges
    IF EXISTS (
        SELECT * 
        FROM [dwh].[dim_customer]
        WHERE expiry_date IS NOT NULL 
            AND expiry_date < effective_date
    )
    BEGIN
        INSERT INTO @ValidationResults
        VALUES ('dim_customer', 'Invalid Date Ranges', 'FAILED', 'Found records with expiry_date < effective_date');
    END
    ELSE
    BEGIN
        INSERT INTO @ValidationResults
        VALUES ('dim_customer', 'Invalid Date Ranges', 'PASSED', 'All date ranges are valid');
    END
    
    -- Validate Product Dimension
    -- Check for duplicate product_ids
    IF EXISTS (
        SELECT product_id, COUNT(*) 
        FROM [dwh].[dim_product]
        GROUP BY product_id
        HAVING COUNT(*) > 1
    )
    BEGIN
        INSERT INTO @ValidationResults
        VALUES ('dim_product', 'Duplicate Product IDs', 'FAILED', 'Found duplicate product_id values');
    END
    ELSE
    BEGIN
        INSERT INTO @ValidationResults
        VALUES ('dim_product', 'Duplicate Product IDs', 'PASSED', 'No duplicate product_ids found');
    END
    
    -- Validate Store Dimension
    -- Check for duplicate current records
    IF EXISTS (
        SELECT store_id, COUNT(*) 
        FROM [dwh].[dim_store]
        WHERE is_current = 1
        GROUP BY store_id
        HAVING COUNT(*) > 1
    )
    BEGIN
        INSERT INTO @ValidationResults
        VALUES ('dim_store', 'Duplicate Current Records', 'FAILED', 'Found duplicate current records for same store_id');
    END
    ELSE
    BEGIN
        INSERT INTO @ValidationResults
        VALUES ('dim_store', 'Duplicate Current Records', 'PASSED', 'No duplicate current records found');
    END
    
    -- Return validation results
    SELECT * FROM @ValidationResults;
    
    -- Check if any validations failed
    IF EXISTS (SELECT * FROM @ValidationResults WHERE check_result = 'FAILED')
    BEGIN
        RAISERROR('Dimension validation failed. Check results above.', 16, 1);
    END
    ELSE
    BEGIN
        PRINT 'All dimension validations passed successfully.';
    END
END
GO


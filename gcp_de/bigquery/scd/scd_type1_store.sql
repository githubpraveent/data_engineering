-- SCD Type 1: Store Dimension Update
-- Overwrites current values (no history tracking)

MERGE `{project_id}.{curated_dataset}.store_dimension` AS target
USING (
    SELECT 
        store_id,
        store_name,
        address,
        city,
        state,
        zip_code,
        country,
        store_manager,
        phone,
        opening_date,
        store_type,
        square_feet,
        CURRENT_TIMESTAMP() AS load_timestamp
    FROM `{project_id}.{staging_dataset}.stores_staging`
    WHERE load_date = DATE('{load_date}')
) AS source
ON target.store_id = source.store_id
WHEN MATCHED THEN
    UPDATE SET
        store_name = source.store_name,
        address = source.address,
        city = source.city,
        state = source.state,
        zip_code = source.zip_code,
        country = source.country,
        store_manager = source.store_manager,
        phone = source.phone,
        store_type = source.store_type,
        square_feet = source.square_feet,
        load_timestamp = source.load_timestamp
WHEN NOT MATCHED THEN
    INSERT (
        store_id,
        store_name,
        address,
        city,
        state,
        zip_code,
        country,
        store_manager,
        phone,
        opening_date,
        store_type,
        square_feet,
        load_timestamp
    )
    VALUES (
        source.store_id,
        source.store_name,
        source.address,
        source.city,
        source.state,
        source.zip_code,
        source.country,
        source.store_manager,
        source.phone,
        source.opening_date,
        source.store_type,
        source.square_feet,
        source.load_timestamp
    );


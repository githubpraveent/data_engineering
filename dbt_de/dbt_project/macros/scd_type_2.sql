{% macro scd_type_2(
    source_table,
    unique_key,
    updated_at_column='updated_at',
    valid_from_column='valid_from',
    valid_to_column='valid_to',
    current_flag_column='current_flag'
) %}

    {# 
        SCD Type 2 implementation macro
        Creates slowly changing dimension with full history tracking
        
        Parameters:
        - source_table: The staging table to process
        - unique_key: The business key (e.g., customer_id)
        - updated_at_column: Column that indicates when record was updated
        - valid_from_column: Name for the valid_from timestamp
        - valid_to_column: Name for the valid_to timestamp
        - current_flag_column: Name for the current flag
    #}

    with source_data as (
        select * from {{ source_table }}
    ),

    existing_dimension as (
        select * from {{ this }}
        where {{ current_flag_column }} = true
    ),

    -- Identify new and changed records
    changes as (
        select
            s.*,
            e.{{ unique_key }} as existing_key,
            case
                when e.{{ unique_key }} is null then 'new'
                when s.{{ updated_at_column }} > e.{{ valid_from_column }} then 'changed'
                else 'unchanged'
            end as change_type
        from source_data s
        left join existing_dimension e
            on s.{{ unique_key }} = e.{{ unique_key }}
    ),

    -- Close out old records
    closed_records as (
        select
            {{ unique_key }},
            {{ valid_from_column }},
            {{ updated_at_column }} as {{ valid_to_column }},
            false as {{ current_flag_column }}
        from existing_dimension
        where {{ unique_key }} in (
            select {{ unique_key }}
            from changes
            where change_type in ('new', 'changed')
        )
    ),

    -- Create new records
    new_records as (
        select
            *,
            {{ updated_at_column }} as {{ valid_from_column }},
            cast(null as timestamp) as {{ valid_to_column }},
            true as {{ current_flag_column }}
        from changes
        where change_type in ('new', 'changed')
    ),

    -- Combine unchanged, closed, and new records
    final as (
        select * from existing_dimension
        where {{ unique_key }} not in (
            select {{ unique_key }} from closed_records
        )
        
        union all
        
        select * from closed_records
        
        union all
        
        select * from new_records
    )

    select * from final

{% endmacro %}


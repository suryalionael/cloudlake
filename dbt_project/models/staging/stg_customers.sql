with source as (
    select * from {{ source('processed', 'customers') }}
),

renamed as (
    select
        customer_id,
        email,
        first_name,
        last_name,
        city,
        state,
        country,
        cast(created_at as timestamp) as created_at,
        cast(updated_at as timestamp) as updated_at
    from source
)

select * from renamed

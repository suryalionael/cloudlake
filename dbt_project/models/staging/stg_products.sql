with source as (
    select * from {{ source('processed', 'products') }}
),

renamed as (
    select
        product_id,
        name as product_name,
        category,
        subcategory,
        cast(price as decimal(10,2)) as price,
        cast(cost as decimal(10,2)) as cost,
        cast(created_at as timestamp) as created_at,
        cast(updated_at as timestamp) as updated_at
    from source
)

select * from renamed

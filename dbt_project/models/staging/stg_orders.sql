with source as (
    select * from {{ source('processed', 'orders') }}
),

renamed as (
    select
        order_id,
        customer_id,
        store_id,
        cast(order_date as timestamp) as order_date,
        status,
        cast(total_amount as decimal(12,2)) as total_amount
    from source
)

select * from renamed

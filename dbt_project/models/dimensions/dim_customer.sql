with customers as (
    select * from {{ ref('stg_customers') }}
),

final as (
    select
        customer_id,
        email,
        first_name,
        last_name,
        concat(first_name, ' ', last_name) as full_name,
        city,
        state,
        country,
        created_at as customer_since,
        updated_at as last_updated
    from customers
)

select * from final

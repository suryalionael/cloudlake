with products as (
    select * from {{ ref('stg_products') }}
),

final as (
    select
        product_id,
        product_name,
        category,
        subcategory,
        price as current_price,
        cost as current_cost,
        case
            when price > 0 then (price - cost) / price * 100
            else 0
        end as margin_percent,
        created_at as product_created_at,
        updated_at as last_updated
    from products
)

select * from final

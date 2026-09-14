with order_items as (
    select * from {{ ref('stg_order_items') }}
),

orders as (
    select * from {{ ref('stg_orders') }}
),

products as (
    select * from {{ ref('dim_product') }}
),

final as (
    select
        oi.order_item_id,
        oi.order_id,
        o.customer_id,
        o.store_id,
        oi.product_id,
        date(o.order_date) as order_date,
        o.order_date as order_timestamp,
        o.status,
        oi.quantity,
        oi.unit_price,
        oi.line_total as revenue,
        o.total_amount as order_total_amount
    from order_items oi
    inner join orders o on oi.order_id = o.order_id
    left join products p on oi.product_id = p.product_id
)

select * from final

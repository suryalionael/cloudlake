with orders as (
    select * from {{ ref('fact_order') }}
    where status = 'complete'
),

final as (
    select
        order_date,
        count(distinct order_id) as order_count,
        count(distinct customer_id) as customer_count,
        sum(quantity) as units_sold,
        sum(revenue) as total_revenue,
        avg(revenue) as avg_line_revenue,
        sum(revenue) / nullif(count(distinct order_id), 0) as avg_order_value
    from orders
    group by order_date
)

select * from final
order by order_date desc

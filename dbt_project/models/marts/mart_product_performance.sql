with products as (
    select * from {{ ref('dim_product') }}
),

orders as (
    select * from {{ ref('fact_order') }}
    where status = 'complete'
),

product_stats as (
    select
        product_id,
        count(distinct order_id) as order_count,
        sum(quantity) as total_units_sold,
        sum(revenue) as total_revenue,
        avg(unit_price) as avg_selling_price,
        rank() over (order by sum(revenue) desc) as revenue_rank,
        rank() over (order by sum(quantity) desc) as volume_rank
    from orders
    group by product_id
),

final as (
    select
        p.product_id,
        p.product_name,
        p.category,
        p.subcategory,
        p.current_price,
        p.margin_percent,
        coalesce(ps.order_count, 0) as order_count,
        coalesce(ps.total_units_sold, 0) as total_units_sold,
        coalesce(ps.total_revenue, 0) as total_revenue,
        ps.avg_selling_price,
        ps.revenue_rank,
        ps.volume_rank
    from products p
    left join product_stats ps on p.product_id = ps.product_id
)

select * from final

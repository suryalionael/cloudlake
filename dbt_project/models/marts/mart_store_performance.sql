with stores as (
    select * from {{ ref('dim_store') }}
),

orders as (
    select * from {{ ref('fact_order') }}
    where status = 'complete'
),

store_stats as (
    select
        store_id,
        count(distinct order_id) as order_count,
        count(distinct customer_id) as customer_count,
        sum(revenue) as total_revenue,
        avg(revenue) as avg_line_revenue,
        rank() over (order by sum(revenue) desc) as revenue_rank
    from orders
    where store_id is not null
    group by store_id
),

final as (
    select
        s.store_id,
        s.store_name,
        s.location,
        s.city,
        s.state,
        s.country,
        s.is_active,
        coalesce(ss.order_count, 0) as order_count,
        coalesce(ss.customer_count, 0) as customer_count,
        coalesce(ss.total_revenue, 0) as total_revenue,
        ss.avg_line_revenue,
        ss.revenue_rank
    from stores s
    left join store_stats ss on s.store_id = ss.store_id
)

select * from final

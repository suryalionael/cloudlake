with customers as (
    select * from {{ ref('dim_customer') }}
),

orders as (
    select * from {{ ref('fact_order') }}
    where status = 'complete'
),

customer_stats as (
    select
        customer_id,
        count(distinct order_id) as total_orders,
        sum(revenue) as lifetime_value,
        avg(revenue) as avg_order_value,
        min(order_date) as first_order_date,
        max(order_date) as last_order_date
    from orders
    group by customer_id
),

final as (
    select
        c.customer_id,
        c.full_name,
        c.email,
        c.city,
        c.state,
        c.country,
        c.customer_since,
        coalesce(cs.total_orders, 0) as total_orders,
        coalesce(cs.lifetime_value, 0) as lifetime_value,
        cs.avg_order_value,
        cs.first_order_date,
        cs.last_order_date,
        case
            when cs.total_orders >= 10 then 'High Frequency'
            when cs.total_orders >= 5 then 'Medium Frequency'
            when cs.total_orders >= 1 then 'Low Frequency'
            else 'No Orders'
        end as frequency_segment,
        case
            when cs.lifetime_value >= 1000 then 'High Value'
            when cs.lifetime_value >= 500 then 'Medium Value'
            when cs.lifetime_value > 0 then 'Low Value'
            else 'No Value'
        end as value_segment
    from customers c
    left join customer_stats cs on c.customer_id = cs.customer_id
)

select * from final

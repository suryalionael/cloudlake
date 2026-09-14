with stores as (
    select * from {{ ref('stg_stores') }}
),

final as (
    select
        store_id,
        store_name,
        city,
        state,
        country,
        concat(city, ', ', state) as location,
        opened_at,
        closed_at,
        is_active
    from stores
)

select * from final

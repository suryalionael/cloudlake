with source as (
    select * from {{ source('processed', 'stores') }}
),

renamed as (
    select
        store_id,
        store_name,
        city,
        state,
        country,
        cast(opened_at as date) as opened_at,
        cast(closed_at as date) as closed_at,
        case when closed_at is null then true else false end as is_active
    from source
)

select * from renamed

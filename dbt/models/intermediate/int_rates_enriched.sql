with staged as (

    select * from {{ ref('stg_exchange_rates') }}

),

enriched as (

    select
        rate_date,
        char_code,
        num_code,
        nominal,
        currency_name,
        rate,
        lag(rate) over (
            partition by char_code order by rate_date
        ) as prev_rate,
        rate - lag(rate) over (
            partition by char_code order by rate_date
        ) as daily_delta,
        case
            when lag(rate) over (partition by char_code order by rate_date) in (0)
                then null
            else round(
                (rate - lag(rate) over (partition by char_code order by rate_date))
                / lag(rate) over (partition by char_code order by rate_date) * 100,
                4
            )
        end as pct_change,
        extract(isodow from rate_date) in (6, 7) as is_weekend
    from staged

)

select * from enriched

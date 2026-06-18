-- One row per currency, carrying its most recent attributes.
with staged as (

    select * from {{ ref('stg_exchange_rates') }}

),

currencies as (

    select distinct on (char_code)
        char_code,
        num_code,
        currency_name,
        nominal
    from staged
    order by char_code, rate_date desc

)

select * from currencies

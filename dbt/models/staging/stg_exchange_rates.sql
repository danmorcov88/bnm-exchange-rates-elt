with source as (

    select * from {{ source('raw', 'exchange_rates') }}

),

cleaned as (

    select
        cast(rate_date as date)              as rate_date,
        upper(trim(char_code))               as char_code,
        nullif(trim(num_code), '')           as num_code,
        nominal,
        trim(name)                           as currency_name,
        cast(value as numeric(18, 6))        as rate,
        loaded_at
    from source

)

select * from cleaned

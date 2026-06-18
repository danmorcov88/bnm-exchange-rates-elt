-- Fact table: one row per (rate_date, char_code) with rate and derived metrics.
with enriched as (

    select * from {{ ref('int_rates_enriched') }}

)

select
    rate_date,
    char_code,
    nominal,
    rate,
    prev_rate,
    daily_delta,
    pct_change,
    is_weekend
from enriched

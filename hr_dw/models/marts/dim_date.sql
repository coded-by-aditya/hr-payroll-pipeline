with dates as (
    select dateadd(day, row_number() over (order by seq4()) - 1, '2026-01-01'::date) as date_day
    from table(generator(rowcount => 730))
)
select
    to_number(to_char(date_day, 'YYYYMMDD'))  as date_key,
    date_day,
    year(date_day)                            as year,
    quarter(date_day)                         as quarter,
    month(date_day)                           as month,
    monthname(date_day)                       as month_name,
    dayname(date_day)                         as day_name,
    date_day = last_day(date_day)             as is_month_end
from dates
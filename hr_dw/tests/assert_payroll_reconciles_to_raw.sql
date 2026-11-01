-- fails if the fact's total pay doesn't match what was loaded into RAW
select f.total as fact_total, r.total as raw_total
from (select sum(amount) as total from {{ ref('fct_payroll') }}) f
cross join (select sum(amount::number(12, 2)) as total from {{ source('raw', 'payroll_lines') }}) r
where f.total <> r.total
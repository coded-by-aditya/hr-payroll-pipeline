select
    pay_run_id,
    to_date(pay_date)                   as pay_date,
    employee_id,
    pay_component,
    amount::number(12, 2)               as amount,
    _source_file,
    _loaded_at
from {{ source('raw', 'payroll_lines') }}
qualify row_number() over (
    partition by pay_run_id, employee_id, pay_component
    order by _loaded_at desc
) = 1
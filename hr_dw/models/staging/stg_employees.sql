select
    employee_id,
    first_name,
    last_name,
    lower(email)                        as email,
    department_code,
    job_title,
    location,
    employment_status,
    try_to_date(hire_date)              as hire_date,
    try_to_date(termination_date)       as termination_date,
    to_timestamp_ntz(last_modified)     as last_modified,
    _loaded_at
from {{ source('raw', 'employees') }}
qualify row_number() over (
    partition by employee_id
    order by last_modified desc, _loaded_at desc
) = 1
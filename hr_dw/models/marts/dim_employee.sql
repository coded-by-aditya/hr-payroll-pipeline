with versions as (
    select * from {{ ref('snap_employees') }}
),

current_details as (
    -- SCD1: name and email always come from the employee's current record
    select employee_id, first_name, last_name, email
    from versions
    where dbt_valid_to is null
)

select
    {{ dbt_utils.generate_surrogate_key(['v.employee_id', 'v.dbt_valid_from']) }} as employee_key,
    v.employee_id,
    c.first_name,
    c.last_name,
    c.email,
    -- SCD2: these keep their history
    v.department_code,
    v.job_title,
    v.location,
    v.employment_status,
    v.hire_date,
    v.termination_date,
    -- first version is valid from the start of time, so early pay runs still match
    case when row_number() over (partition by v.employee_id order by v.dbt_valid_from) = 1
         then '1900-01-01'::timestamp_ntz else v.dbt_valid_from end           as valid_from,
    coalesce(v.dbt_valid_to, '9999-12-31'::timestamp_ntz)                     as valid_to,
    v.dbt_valid_to is null                                                    as is_current
from versions v
join current_details c on v.employee_id = c.employee_id
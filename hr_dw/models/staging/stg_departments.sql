select
    department_code,
    department_name,
    cost_centre

from {{ source('raw', 'departments') }}
qualify row_number() over (
    partition by department_code
    order by _loaded_at desc
) = 1
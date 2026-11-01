select
    {{ dbt_utils.generate_surrogate_key(['department_code']) }} as department_key,
    department_code,
    department_name,
    cost_centre
from {{ ref('stg_departments') }}
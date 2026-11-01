with pay as (
    select * from {{ ref('stg_payroll_lines') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['pay.pay_run_id', 'pay.employee_id', 'pay.pay_component']) }} as payroll_line_key,
    pay.pay_run_id,                                          -- degenerate dimension
    to_number(to_char(pay.pay_date, 'YYYYMMDD'))  as date_key,
    emp.employee_key,
    dept.department_key,
    pc.pay_component_key,
    pay.amount                                               -- the fact
from pay
left join {{ ref('dim_employee') }} emp
    on  pay.employee_id = emp.employee_id
    and pay.pay_date >= emp.valid_from                       -- point-in-time join:
    and pay.pay_date <  emp.valid_to                         -- the version valid on the pay date
left join {{ ref('dim_department') }} dept
    on emp.department_code = dept.department_code            -- department at the time of pay
left join {{ ref('dim_pay_component') }} pc
    on pay.pay_component = pc.pay_component
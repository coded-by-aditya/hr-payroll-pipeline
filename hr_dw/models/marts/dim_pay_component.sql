select
    {{ dbt_utils.generate_surrogate_key(['pay_component']) }} as pay_component_key,
    pay_component,
    description,
    component_group
from (values
    ('BASE',     'Base pay',            'Earnings'),
    ('OVERTIME', 'Overtime',            'Earnings'),
    ('TAX',      'Income tax withheld', 'Deductions'),
    ('SUPER',    'Superannuation',      'Employer contributions')
) as t (pay_component, description, component_group)
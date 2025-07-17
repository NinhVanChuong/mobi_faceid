SELECT 
    a.id AS emp_id, 
    a.name AS emp_name, 
    (b.check_in AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Bangkok')::DATE AS check_in_date,
    b.check_in AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Bangkok',
    b.status,
    c.name->>'en_US' as department_name,
    d.name->>'en_US' as department_parent_name
FROM hr_employee a
LEFT JOIN hr_attendance b ON a.id = b.employee_id
LEFT JOIN hr_department c ON a.department_id = c.id
LEFT JOIN hr_department d ON c.parent_id = d.id
WHERE b.status = 'late'
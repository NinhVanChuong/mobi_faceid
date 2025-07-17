SELECT 
    a.id AS emp_id, 
    a.name AS emp_name, 
    DATE_TRUNC('month', (b.check_in AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Bangkok')::DATE) AS check_in_month,
    b.status,
    c.name->>'en_US' AS department_name,
    d.name->>'en_US' AS department_parent_name,
    COUNT(*) AS "Số lần đi muộn"
FROM hr_employee a
LEFT JOIN hr_attendance b ON a.id = b.employee_id
LEFT JOIN hr_department c ON a.department_id = c.id
LEFT JOIN hr_department d ON c.parent_id = d.id
WHERE b.status = 'late'
GROUP BY emp_id, emp_name, check_in_month, b.status, department_name, department_parent_name
ORDER BY "Số lần đi muộn" DESC;

WITH thanh_pho_late AS (
    SELECT
        (b.check_in AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Bangkok')::DATE AS check_in_date,
        b.status,
        d.id as department_id,
        d.name->>'en_US' as department_name,
        COUNT(*) as count_late
    FROM hr_employee a
    LEFT JOIN hr_attendance b ON a.id = b.employee_id
    LEFT JOIN hr_department c ON a.department_id = c.id
    LEFT JOIN hr_department d ON c.parent_id = d.id
    WHERE b.status = 'late'
    GROUP BY department_name, check_in_date, d.id, b.status
),

thanh_pho_total AS (
    SELECT d.parent_id as department_id, COUNT(*) AS total 
    FROM hr_employee a
    LEFT JOIN hr_department d ON a.department_id = d.id
    WHERE d.parent_id NOT IN (1,4,125)
    AND department_id != 1
    GROUP BY d.parent_id
)

SELECT 
    a.check_in_date AS "Ngày", 
    a.department_name AS "Đơn vị", 
    a.count_late AS "Muộn", 
    b.total AS "Tổng",
    ROUND((a.count_late::NUMERIC / NULLIF(b.total, 0)) * 100, 2) AS "Tỉ lệ (%)"
FROM thanh_pho_late a
JOIN thanh_pho_total b ON a.department_id = b.department_id;
-- WHERE check_in_date = {{DATE}};

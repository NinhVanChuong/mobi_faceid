WITH
  cua_hang_late AS (
    SELECT
      (
        b.check_in AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Bangkok'
      )::DATE AS check_in_date,
      b.status,
      c.name ->> 'en_US' AS department_name,
      c.id AS department_id,
      COUNT(*) AS count_late
    FROM
      hr_employee a
      JOIN hr_attendance b ON a.id = b.employee_id
      LEFT JOIN hr_department c ON a.department_id = c.id
    WHERE
      b.status = 'late'
    GROUP BY
      department_name,
      check_in_date,
      c.id,
      b.status
  ),
  cua_hang_total AS (
    SELECT
      department_id,
      COUNT(*) AS total
    FROM
      hr_employee
    WHERE
      department_id NOT IN (1,5,119,120,121,122,126,127,128,129,130,131,132,133,134,135,136) 
    GROUP BY
      department_id
  )
SELECT
  a.check_in_date AS "Ngày",
  a.department_name AS "Đơn vị",
  a.count_late AS "Muộn",
  b.total AS "Tổng",
  ROUND((a.count_late::NUMERIC / NULLIF(b.total, 0)) * 100, 2) AS "Tỉ lệ (%)"
FROM
  cua_hang_late a
  JOIN cua_hang_total b ON a.department_id = b.department_id;
-- WHERE
--   a.check_in_date = {{DATE}};

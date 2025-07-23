from odoo import api, fields, models

class HrDepartment(models.Model):
    _inherit = 'hr.department'

    @api.model
    def get_child_departments(self):
        """
        Lấy danh sách các đơn vị con của đơn vị người dùng hiện tại
        Nếu người dùng thuộc phòng ban "Administration" thì trả về tất cả phòng ban
        """
        user = self.env.user
        employee = user.employee_id
        if not employee or not employee.department_id:
            return []
            
        user_department = employee.department_id
        
        # if user.has_group('hr.group_hr_manager'):
        #     all_departments = self.search([]) - user_department
        #     return all_departments.read(['id', 'name'])
        #
        # elif user.has_group('hikvision_minmoe.hr_department_officer'):
        #     employee_manage_department_ids = employee.manage_department_ids - user_department
        #     return employee_manage_department_ids.read(['id', 'name'])
        # else:
        return []
from odoo import api, fields, models

class HrDepartment(models.Model):
    _inherit = 'hr.department'

    @api.model
    def get_child_departments(self):
        """
        Lấy danh sách các đơn vị con của đơn vị người dùng hiện tại
        Nếu người dùng thuộc phòng ban "Administration" thì trả về tất cả phòng ban
        """
        # Lấy nhân viên hiện tại
        employee = self.env.user.employee_id
        if not employee or not employee.department_id:
            return []
            
        # Lấy đơn vị của nhân viên
        user_department = employee.department_id
        
        # Kiểm tra nếu người dùng thuộc phòng ban "Administrator"
        if user_department.name in ["Administration", "Quản trị"]:
            # Trả về tất cả các phòng ban
            all_departments = self.search([])
            return all_departments.read(['id', 'name'])
        
        # Lấy tất cả các đơn vị con của đơn vị người dùng
        child_departments = self.search([('id', 'child_of', user_department.id), ('id', '!=', user_department.id)])
        
        # Trả về danh sách các đơn vị con với id và name
        return child_departments.read(['id', 'name']) 
from odoo import models, fields, api, exceptions, _
import logging

_logger = logging.getLogger(__name__)

class HrEmployee(models.Model):
    _name = "hr.employee"
    _inherit = "hr.employee"

    # employee_id_hik = fields.Integer(string="Employee id in Hik device", default=0)
    emp_code_mobifone = fields.Char(string="Mobifone Emp Code")
    zalo_oa_access_token = fields.Char(related='department_id.zalo_oa_id.access_token',store=False)
    zalo_user_id = fields.Char()
    zalo_register_status = fields.Selection(selection=[('registered', 'Đã đăng ký Zalo'), ('not_registered', 'Chưa đăng ký Zalo')], store=False,compute='_compute_zalo_register_status')
    # zalo_oa_id = fields.Many2one('zalo.oa')

    shift_id = fields.Many2one('hr.attendance.shift', string="Ca làm việc")
    show_attendance_report = fields.Boolean(string="Hiển thị báo cáo điểm danh", default=True)

    telegram_user_id = fields.Char()

    def search_debug(self):
        department_ids = self.env.user.employee_id.manage_department_ids.ids if self.env.user.employee_id else [0]
        _logger.info(f'Department IDs: {department_ids}')
        return department_ids

    def _compute_zalo_register_status(self):
        for r in self:
            if not r.zalo_user_id:
                r.zalo_register_status = 'not_registered'
            else:
                r.zalo_register_status = 'registered'

    

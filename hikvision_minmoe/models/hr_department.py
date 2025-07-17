from odoo import api, fields, models, _

class Department(models.Model):
    _inherit = "hr.department"

    zalo_oa_id = fields.Many2one('zalo.oa',string='Zalo Official Account')
    shop_code = fields.Char()

    shift_id = fields.Many2one('hr.attendance.shift', string="Ca làm việc")

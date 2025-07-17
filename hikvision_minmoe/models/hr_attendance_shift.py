from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta
from odoo.tools import format_datetime
class HrAttendanceShift(models.Model):
    _name = "hr.attendance.shift"

    name = fields.Char()
    hour_from = fields.Float(string='Work from', required=True, index=True,
        help="Start and End time of working.\n"
             "A specific value of 24:00 is interpreted as 23:59:59.999999.")
    hour_to = fields.Float(string='Work to', required=True)

    department_ids = fields.One2many('hr.department','shift_id')
    employee_ids = fields.One2many('hr.employee','shift_id')
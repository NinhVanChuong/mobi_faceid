from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class HrAttendanceShiftRegister(models.Model):
    _name = 'hr.attendance.shift.register'
    _description = 'Đăng ký ca làm việc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    employee_id = fields.Many2one('hr.employee', string='Nhân viên', required=True, tracking=True)
    week_start_date = fields.Date(string='Ngày bắt đầu tuần', required=True, tracking=True)
    week_end_date = fields.Date(string='Ngày kết thúc tuần', compute='_compute_week_end_date', store=True, readonly=True)
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Đã xác nhận'),
        ('done', 'Hoàn thành')
    ], string='Trạng thái', default='draft', tracking=True)
    
    shift_lines = fields.One2many('hr.attendance.shift.register.line', 'register_id', string='Chi tiết ca làm việc')
    
    @api.depends('week_start_date')
    def _compute_week_end_date(self):
        for record in self:
            if record.week_start_date:
                # Tính ngày kết thúc là 6 ngày sau ngày bắt đầu
                record.week_end_date = record.week_start_date + timedelta(days=6)
    
    @api.constrains('week_start_date')
    def _check_week_start_date(self):
        for record in self:
            if record.week_start_date and record.week_start_date.weekday() != 0:  # Monday is 0
                raise ValidationError(_('Ngày bắt đầu tuần phải là thứ 2'))
    
    @api.onchange('week_start_date')
    def _onchange_week_dates(self):
        if self.week_start_date:
            # Xóa các dòng cũ nếu có
            self.shift_lines = [(5, 0, 0)]
            
            # Tạo các dòng mới
            lines = []
            current_date = self.week_start_date
            end_date = self.week_start_date + timedelta(days=6)
            while current_date <= end_date:
                lines.append((0, 0, {
                    'date': current_date,
                    'check_in': '07:30',
                    'check_out': '17:00',
                }))
                current_date += timedelta(days=1)
            
            self.shift_lines = lines
    
    def action_confirm(self):
        for record in self:
            if not record.shift_lines:
                raise ValidationError(_('Vui lòng đăng ký ca làm việc cho tất cả các ngày trong tuần'))
            for line in record.shift_lines:
                if not line.check_in or not line.check_out:
                    raise ValidationError(_('Vui lòng nhập đầy đủ giờ vào và giờ ra cho tất cả các ngày'))
            record.state = 'confirmed'
    
    def action_done(self):
        self.state = 'done'

class HrAttendanceShiftRegisterLine(models.Model):
    _name = 'hr.attendance.shift.register.line'
    _description = 'Chi tiết ca làm việc'
    
    register_id = fields.Many2one('hr.attendance.shift.register', string='Đăng ký ca làm việc', required=True, ondelete='cascade')
    date = fields.Date(string='Ngày', required=True)
    check_in = fields.Char(string='Giờ vào', required=True)
    check_out = fields.Char(string='Giờ ra', required=True)
    
    @api.constrains('check_in', 'check_out')
    def _check_shift_duration(self):
        for record in self:
            if record.check_in and record.check_out:
                try:
                    check_in_time = datetime.strptime(record.check_in, '%H:%M')
                    check_out_time = datetime.strptime(record.check_out, '%H:%M')
                    duration = (check_out_time - check_in_time).total_seconds() / 3600
                    if duration < 8:
                        raise ValidationError(_('Thời gian làm việc phải tối thiểu 8 tiếng'))
                except ValueError:
                    raise ValidationError(_('Định dạng giờ không hợp lệ. Vui lòng sử dụng định dạng HH:MM')) 
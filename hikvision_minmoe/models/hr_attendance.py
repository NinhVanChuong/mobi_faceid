from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta, timezone
# from odoo.tools import format_datetime
import threading
import telegram
import base64
#telegram
telegram_bot_token='7699059550:AAH0ztiK7wb_dfayFD3yWhIapQBIpitIic0' #TTKDCNS_bot. 
telegram_bot = telegram.Bot(token=telegram_bot_token) 

def send_image_to_telegram(chat_id,image_checkin,tele_mess):
    image_checkin_string = base64.b64decode(image_checkin)
    telegram_bot.send_photo(chat_id=chat_id, photo=image_checkin_string,caption=tele_mess)

class HrAttendance(models.Model):
    _name = "hr.attendance"
    _inherit = "hr.attendance"


    image_checkin = fields.Image(max_width=1920,max_height=1080,required=False)
    image_checkout = fields.Image(max_width=1920,max_height=1080,required=False)


    status = fields.Selection(selection=[
                ('late', 'Muộn'),
                ('right_time', 'Đúng giờ'),
                ('time_off','Nghỉ phép'),
                ('business_trip','Đi công tác'),
                ('none','Chưa điểm danh')
                ], string='Trạng thái',compute='_compute_status',store=True
        )
  
    @api.depends('check_in')
    def _compute_status(self):
        for r in self:
            check_in = r.check_in + timedelta(hours=7)
            check_in_float = check_in.hour + check_in.minute / 60
            hour_from = r.employee_id.shift_id.hour_from
            hour_from = hour_from if hour_from != 0.0 else 8.0
            if check_in_float >= hour_from:
                r.status = "late"
            else:
                r.status = "right_time"


    def create_check_in_out(self,employee_id,check_in_time,image_checkin):
        # Chuyển check_in_time về giờ Việt Nam để tính ngày đúng
        vn_time = check_in_time + timedelta(hours=7)
        vn_date = vn_time.date()
        
        # Tính start_of_day và end_of_day theo giờ Việt Nam, sau đó chuyển về UTC
        start_of_day_vn = datetime.combine(vn_date, datetime.min.time())
        end_of_day_vn = datetime.combine(vn_date, datetime.max.time())
        
        # Chuyển về UTC để tìm kiếm trong database
        start_of_day = start_of_day_vn - timedelta(hours=7)
        end_of_day = end_of_day_vn - timedelta(hours=7)
        
        # Tìm bản ghi có check_in sớm nhất trong ngày của nhân viên
        record_id = self.search([('employee_id','=',employee_id),
                                 ('check_in','>=',start_of_day),
                                 ('check_in','<=',end_of_day)
                                 ], order='check_in asc', limit=1)
        if not record_id.id:
            # Tạo bản ghi check in
            vals = {
                'employee_id': employee_id,
                'check_in': check_in_time,#fields.Datetime.now(),
                'image_checkin': image_checkin
            }
            result = self.create(vals)
            return 'check_in',result.status
            

            # #send message to telegram
            # employee = self.env['hr.employee'].browse(employee_id)
            # if employee.telegram_user_id:
            #     chat_id = employee.telegram_user_id
            #     tele_mess = f"{employee.job_title} {employee.name} đã có mặt vào lúc {check_in_time + timedelta(hours=7)}"
            #     # Run in a separate thread
            #     thread = threading.Thread(target=send_image_to_telegram, args=(chat_id,image_checkin,tele_mess,))
            #     thread.start()
        else:
            # Cập nhật bản ghi check out
            record_id.write({
                "check_out": check_in_time,
                "image_checkout": image_checkin
            })
        
            return 'check_out',record_id.status

    

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        """ Verifies the validity of the attendance record compared to the others from the same employee.
            For the same employee we must have :
                * maximum 1 "open" attendance record (without check_out)
                * no overlapping time slices with previous employee records
        """

        # for attendance in self:
        #     # we take the latest attendance before our check_in time and check it doesn't overlap with ours
        #     last_attendance_before_check_in = self.env['hr.attendance'].search([
        #         ('employee_id', '=', attendance.employee_id.id),
        #         ('check_in', '<=', attendance.check_in),
        #         ('id', '!=', attendance.id),
        #     ], order='check_in desc', limit=1)
        #     if last_attendance_before_check_in and last_attendance_before_check_in.check_out and last_attendance_before_check_in.check_out > attendance.check_in:
        #         raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s",
        #                                            empl_name=attendance.employee_id.name,
        #                                            datetime=format_datetime(self.env, attendance.check_in, dt_format=False)))

        #     if not attendance.check_out:
        #         # if our attendance is "open" (no check_out), we verify there is no other "open" attendance
        #         no_check_out_attendances = self.env['hr.attendance'].search([
        #             ('employee_id', '=', attendance.employee_id.id),
        #             ('check_out', '=', False),
        #             ('id', '!=', attendance.id),
        #         ], order='check_in desc', limit=1)
        #         if no_check_out_attendances:
        #             raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee hasn't checked out since %(datetime)s",
        #                                                empl_name=attendance.employee_id.name,
        #                                                datetime=format_datetime(self.env, no_check_out_attendances.check_in, dt_format=False)))
        #     else:
        #         # we verify that the latest attendance with check_in time before our check_out time
        #         # is the same as the one before our check_in time computed before, otherwise it overlaps
        #         last_attendance_before_check_out = self.env['hr.attendance'].search([
        #             ('employee_id', '=', attendance.employee_id.id),
        #             ('check_in', '<', attendance.check_out),
        #             ('id', '!=', attendance.id),
        #         ], order='check_in desc', limit=1)
        #         if last_attendance_before_check_out and last_attendance_before_check_in != last_attendance_before_check_out:
        #             raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s",
        #                                                empl_name=attendance.employee_id.name,
        #                                                datetime=format_datetime(self.env, last_attendance_before_check_out.check_in, dt_format=False)))

# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ranjith R(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
###############################################################################
import pandas
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.http import request
from odoo.tools import date_utils
import pytz
import base64
import tempfile
import os
import xlwt


class HrEmployee(models.Model):
    """This module extends the 'hr.employee' model of  Odoo Employees Module.
     It adds a new method called 'get_employee_leave_data', which is used to
     retrieve data for the dashboard."""
    _inherit = 'hr.employee'
    _check_company_auto = True

    @api.model
    def get_employee_leave_data(self, params):
        """Returns data to the dashboard"""
        employee_data = []
        # Thay đổi: Lấy cấu hình từ ir.config_parameter thay vì res.config.settings
        present_mark = self.env['ir.config_parameter'].sudo().get_param(
            'advance_hr_attendance_dashboard.present', '\u2714')
        absent_mark = self.env['ir.config_parameter'].sudo().get_param(
            'advance_hr_attendance_dashboard.absent', '\u2716')
        
        dates = False
        department_ids = False
        
        # Xử lý params
        if isinstance(params, dict):
            duration = params.get('duration')
            department_ids = params.get('department_ids')  # Thay đổi từ department_id thành department_ids
        else:
            # Để tương thích với code cũ
            duration = params

        # Xử lý lọc theo thời gian
        if duration == 'this_week':
            dates = pandas.date_range(
                date_utils.start_of(fields.Date.today(), 'week'),
                date_utils.end_of(fields.Date.today(), 'week')
                - timedelta(days=0),
                freq='d').strftime("%Y-%m-%d").tolist()
        elif duration == 'this_month':
            dates = pandas.date_range(
                date_utils.start_of(fields.Date.today(), 'month'),
                date_utils.end_of(fields.Date.today(), 'month')
                - timedelta(days=0),
                freq='d').strftime("%Y-%m-%d").tolist()
        elif duration == 'last_month':
            dates = pandas.date_range(
                date_utils.start_of(fields.Date.today()- relativedelta(months=1), 'month'),
                date_utils.end_of(fields.Date.today()- relativedelta(months=1), 'month'),
                freq='d').strftime("%Y-%m-%d").tolist()
        elif duration == 'last_15_days':
            dates = [str(date.today() - timedelta(days=day))
                     for day in range(15)]
        elif duration and '-' in duration:  # Xử lý định dạng YYYY-MM
            year, month = map(int, duration.split('-'))
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
            dates = pandas.date_range(start_date, end_date, freq='d').strftime("%Y-%m-%d").tolist()
        else:
            # Mặc định lấy tháng hiện tại
            dates = pandas.date_range(
                date_utils.start_of(fields.Date.today(), 'month'),
                date_utils.end_of(fields.Date.today(), 'month')
                - timedelta(days=0),
                freq='d').strftime("%Y-%m-%d").tolist()

        cids = request.httprequest.cookies.get('cids')
        allowed_company_ids = [int(cid) for cid in cids.split(',')]
        
        # Lọc theo phòng ban nếu có
        domain = [('company_id', 'in', allowed_company_ids)]
        if department_ids:
            # Chỉ lấy nhân viên thuộc đơn vị được chọn, không lấy đơn vị con
            domain.append(('department_id', 'in', department_ids))
        else:
            # Nếu không chọn đơn vị, chỉ hiển thị nhân viên thuộc đơn vị của người dùng và các đơn vị con
            user_employee = self.env.user.employee_id
            if user_employee and user_employee.department_id:
                user_department = user_employee.department_id
                child_departments = self.env['hr.department'].search([
                    ('id', 'child_of', user_department.id)
                ])
                domain.append(('department_id', 'in', child_departments.ids))

        domain.append(('show_attendance_report', '=', True))
        employees = self.env['hr.employee'].search(domain)
        for employee in employees:
            leave_data = []
            employee_present_dates = []
            employee_leave_dates = []
            total_absent_count = 0
            total_present_count = 0
            query = ("""
                SELECT hl.id,employee_id,request_date_from,request_date_to,
                hlt.leave_code,hlt.color
                FROM hr_leave hl
                INNER JOIN hr_leave_type hlt ON hlt.id = hl.holiday_status_id 
                WHERE hl.state = 'validate' AND employee_id = '%s'"""
                     % employee.id)
            self._cr.execute(query)
            all_leave_rec = self._cr.dictfetchall()
            for leave in all_leave_rec:
                leave_dates = pandas.date_range(
                    leave.get('request_date_from'),
                    leave.get('request_date_to') - timedelta(
                        days=0),
                    freq='d').strftime(
                    "%Y-%m-%d").tolist()
                leave_dates.insert(0, leave.get('leave_code'))
                leave_dates.insert(1, leave.get('color'))
                for leave_date in leave_dates:
                    if leave_date in dates:
                        employee_leave_dates.append(
                            leave_date
                        )
            for employee_check_in in employee.attendance_ids:
                employee_present_dates.append(
                    str(employee_check_in.check_in.date()))
            for leave_date in dates:
                color = "#ffffff"
                state = None
                
                # Kiểm tra xem có phải ngày cuối tuần không
                date_obj = datetime.strptime(leave_date, '%Y-%m-%d')
                is_weekend = date_obj.weekday() >= 5  # 5 là thứ 7, 6 là chủ nhật
                
                if not is_weekend:  # Chỉ đánh dấu nếu không phải ngày cuối tuần
                    # Thay đổi: Sử dụng giá trị từ ir.config_parameter
                    if leave_date in employee_present_dates:
                        state = present_mark
                        total_present_count +=1
                    else:
                        state = absent_mark
                    if leave_date in employee_leave_dates:
                        state = leave_dates[0]
                        color = "#F06050" if leave_dates[1] == 1 \
                            else "#F4A460" if leave_dates[1] == 2 \
                            else "#F7CD1F" if leave_dates[1] == 3 \
                            else "#6CC1ED" if leave_dates[1] == 4 \
                            else "#814968" if leave_dates[1] == 5 \
                            else "#EB7E7F" if leave_dates[1] == 6 \
                            else "#2C8397" if leave_dates[1] == 7 \
                            else "#475577" if leave_dates[1] == 8 \
                            else "#D6145F" if leave_dates[1] == 9 \
                            else "#30C381" if leave_dates[1] == 10 \
                            else "#9365B8" if leave_dates[1] == 11 \
                            else "#ffffff"
                        total_absent_count += 1
                
                leave_data.append({
                    'id': employee.id,
                    'leave_date': leave_date,
                    'state': state,
                    'color': color,
                    'sort_key': leave_date or '9999-12-31 23:59:59'
                })
            employee_data.append({
                'id': employee.id,
                'name': employee.name,
                'department_id': employee.department_id.name,
                'leave_data': leave_data,
                'total_absent_count': total_absent_count,
                'total_present_count': total_present_count
            })
        return {
            'employee_data': employee_data,
            'filtered_duration_dates': dates
        }

    @api.model
    def get_employee_attendance_data(self, params):
        """Lấy dữ liệu điểm danh của nhân viên theo ngày cụ thể"""
        selected_date = params.get('selected_date')
        department_ids = params.get('department_ids')  # Thay đổi từ department_id thành department_ids
        search_query = params.get('search_query')
        selected_status = params.get('status', [])
        
        if not selected_date:
            # Nếu không có ngày được chọn, sử dụng ngày hiện tại
            selected_date = fields.Date.today()
        
        # Xây dựng domain
        domain = []
        if department_ids:
            # Chỉ lấy nhân viên thuộc đơn vị được chọn, không lấy đơn vị con
            domain.append(('department_id', 'in', department_ids))
        if search_query:
            domain.append(('name', 'ilike', search_query))

        domain.append(('show_attendance_report', '=', True))
        employees = self.env['hr.employee'].search(domain)
        
        # Chuyển đổi ngày thành datetime
        try:
            if isinstance(selected_date, str):
                selected_date = fields.Date.from_string(selected_date)
            date_from = datetime.combine(selected_date, datetime.min.time())
            date_to = datetime.combine(selected_date, datetime.max.time())
            
            # Lấy múi giờ Việt Nam
            vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
            
            # Chuyển đổi date_from và date_to từ naive datetime sang aware datetime với múi giờ Việt Nam
            date_from = vietnam_tz.localize(date_from)
            date_to = vietnam_tz.localize(date_to)
            
            # Chuyển đổi về UTC để so sánh với check_in (vì check_in được lưu ở UTC trong database)
            date_from = date_from.astimezone(pytz.UTC)
            date_to = date_to.astimezone(pytz.UTC)
        except Exception as e:
            return []
        
        employee_data = []
        for employee in employees:
            # Lấy bản ghi chấm công trong ngày
            attendance = self.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', date_from),
                ('check_in', '<=', date_to)
            ], limit=1)
            
            # Lấy bản ghi nghỉ phép
            time_off = self.env['hr.leave'].search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'validate'),
                ('holiday_status_id.name', 'ilike', 'Nghỉ phép'),
                ('request_date_from', '<=', selected_date),
                ('request_date_to', '>=', selected_date)
            ], limit=1)
            
            # Lấy bản ghi công tác
            business_trip = self.env['hr.leave'].search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'validate'),
                ('holiday_status_id.name', 'ilike', 'Đi công tác'),
                ('request_date_from', '<=', selected_date),
                ('request_date_to', '>=', selected_date)
            ], limit=1)

            status = 'none'  # Mặc định là chưa điểm danh
            check_in = None
            check_in_vietnam = None

            if time_off:
                status = 'time_off'
            elif business_trip:
                status = 'business_trip'
            elif attendance:
                check_in = attendance.check_in
                # Chuyển đổi thời gian sang múi giờ Việt Nam
                if check_in:
                    utc_dt = pytz.utc.localize(check_in)
                    vietnam_dt = utc_dt.astimezone(vietnam_tz)
                    check_in_vietnam = vietnam_dt.strftime('%H:%M:%S %d/%m/%Y')
                status = attendance.status  # 'late' hoặc 'right_time'

            # Bỏ qua nếu trạng thái không nằm trong danh sách được chọn
            if selected_status and status not in selected_status:
                continue

            # Chuyển check_in thành chuỗi để so sánh
            check_in_str = check_in.strftime('%Y-%m-%d %H:%M:%S') if check_in else '9999-12-31 23:59:59'

            employee_data.append({
                'name': employee.name,
                'department_id': employee.department_id.name,
                'check_in': check_in_vietnam,
                'status': status,
                'sort_key': check_in_str
            })

        # Sắp xếp dữ liệu: null lên đầu, sau đó sắp xếp theo thời gian giảm dần
        sorted_data = sorted(employee_data, key=lambda x: x['sort_key'], reverse=True)
        
        # Loại bỏ sort_key trước khi trả về
        for item in sorted_data:
            item.pop('sort_key', None)
            
        return sorted_data

    @api.model
    def print_attendance_report_daily(self, params):
        """In báo cáo PDF"""
        selected_date = params.get('selected_date')
        department_ids = params.get('department_ids')  # Thay đổi từ department_id thành department_ids
        selected_status = params.get('status')
        
        # Xây dựng domain
        domain = []
        if department_ids:
            # Chỉ lấy nhân viên thuộc đơn vị được chọn, không lấy đơn vị con
            domain.append(('department_id', 'in', department_ids))
            
        data = {
            'domain': domain,
            'selected_date': selected_date,
            'status': selected_status
        }
        return self.env.ref('advance_hr_attendance_dashboard.action_report_attendance_daily').report_action(self, data=data)

    @api.model
    def export_attendance_excel(self, params):
        # Lấy dữ liệu từ dashboard
        result = self.get_employee_leave_data(params)
        employee_data = result['employee_data']
        dates = result['filtered_duration_dates']
        

        # Tạo workbook và worksheet mới
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Báo cáo chấm công')
        
        # Định dạng cho tiêu đề
        header_style = xlwt.easyxf('font: bold on; align: horiz center; pattern: pattern solid, fore_colour gray25;')
        date_style = xlwt.easyxf('font: bold on; align: horiz center;')
        cell_style = xlwt.easyxf('align: horiz center;')
        
        # Thiết lập độ rộng cột
        worksheet.col(0).width = 8000  # Họ và tên
        worksheet.col(1).width = 6000  # Đơn vị
        for i in range(len(dates)):
            worksheet.col(i + 2).width = 3000  # Các cột ngày
        worksheet.col(len(dates) + 2).width = 3000  # Cột Total
        
        # Viết tiêu đề cố định
        worksheet.write(0, 0, 'Họ và tên', header_style)
        worksheet.write(0, 1, 'Đơn vị', header_style)
        
        # Viết tiêu đề các ngày
        for col, date_str in enumerate(dates, start=2):
            # Chuyển đổi định dạng ngày
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%d-%b-%Y').upper()  # Ví dụ: 01-JAN-2024
            worksheet.write(0, col, formatted_date, date_style)
        
        # Viết tiêu đề Total
        worksheet.write(0, len(dates) + 2, 'Total', header_style)
        
        # Viết dữ liệu
        for row, employee in enumerate(employee_data, start=1):
            # Ghi tên và đơn vị
            worksheet.write(row, 0, employee['name'])
            worksheet.write(row, 1, employee['department_id'])
            
            # Ghi dữ liệu điểm danh theo từng ngày
            for col, leave_data in enumerate(employee['leave_data'], start=2):
                if col - 2 < len(dates):  # Kiểm tra để tránh vượt quá số cột
                    state = leave_data.get('state', '')
                    worksheet.write(row, col, state or '', cell_style)
            
            # Ghi tổng số ngày có mặt
            worksheet.write(row, len(dates) + 2, employee['total_present_count'], cell_style)
        
        # Lưu file tạm thời
        file_path = tempfile.mktemp(suffix='.xls')
        workbook.save(file_path)
        
        # Đọc file và chuyển thành base64
        with open(file_path, 'rb') as file:
            file_data = base64.b64encode(file.read())
            
        # Xóa file tạm
        os.unlink(file_path)
        
        # Tạo tên file với tháng được chọn
        selected_month = params.get('duration', datetime.now().strftime('%Y-%m'))
        filename = f'Bao_cao_cham_cong_{selected_month}.xls'
        
        # Tạo attachment
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': file_data,
            'res_model': self._name,
            'res_id': 0,
            'mimetype': 'application/vnd.ms-excel'
        })
        
        # Trả về URL để download file
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    @api.model
    def export_attendance_daily_excel(self, params):
        """Xuất báo cáo Excel cho báo cáo ngày"""
        # Lấy dữ liệu từ báo cáo ngày
        employee_data = self.get_employee_attendance_data(params)
        selected_date = params.get('selected_date', fields.Date.today())
        
        # Thêm thông tin đơn vị cha vào dữ liệu nhân viên và sắp xếp theo đơn vị cha trước
        for employee in employee_data:
            department_name = employee['department_id']
            # Tìm đơn vị trong hệ thống để lấy thông tin đơn vị cha
            department_record = self.env['hr.department'].search([('name', '=', department_name)], limit=1)
            parent_department_name = department_record.parent_id.name if department_record and department_record.parent_id else ''
            employee['parent_department'] = parent_department_name
        
        # Sắp xếp employee_data theo đơn vị cha, đơn vị con, và tên nhân viên
        employee_data.sort(key=lambda x: (
            x['parent_department'] or 'ZZZ',  # Đơn vị không có cha sẽ xuống cuối
            x['department_id'] or '',
            x['name'] or ''
        ))
        
        # Tạo workbook và worksheet mới
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Báo cáo ngày')
        
        # Định dạng cho tiêu đề
        header_style = xlwt.easyxf(
            'font: bold on; align: horiz center; borders: left thin, right thin, top thin, bottom thin;'
        )
        cell_style = xlwt.easyxf(
            'align: horiz center; borders: left thin, right thin, top thin, bottom thin;'
        )
        title_style = xlwt.easyxf(
            'font: bold on, height 320; align: horiz center;'
        )
        date_style = xlwt.easyxf(
            'font: bold on; align: horiz center; borders: left thin, right thin, top thin, bottom thin;'
        )
        department_header_style = xlwt.easyxf(
            'font: bold on; pattern: pattern solid,fore_colour gray25; borders: left thin, right thin, top thin, bottom thin;'
        )
        parent_department_header_style = xlwt.easyxf(
            'font: bold on; pattern: pattern solid,fore_colour light_blue; borders: left thin, right thin, top thin, bottom thin;'
        )

        # Gộp các ô cho tiêu đề chính
        worksheet.write_merge(0, 0, 0, 3, 'BẢNG THỐNG KÊ CHẤM CÔNG', title_style)
        
        # Thêm ngày xuất báo cáo
        if isinstance(selected_date, str):
            # Đầu tiên parse theo định dạng gốc
            date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
            # Sau đó format lại theo định dạng mong muốn
            formatted_date = date_obj.strftime('%d-%m-%Y')
        else:
            # Nếu là date object, format trực tiếp
            formatted_date = selected_date.strftime('%d-%m-%Y')
            
        worksheet.write_merge(1, 1, 0, 3, f'Ngày: {formatted_date}', date_style)
        
        # Thiết lập độ rộng cột
        worksheet.col(0).width = 3000   # STT
        worksheet.col(1).width = 8000   # Họ và tên
        worksheet.col(2).width = 6000   # Thời gian vào
        worksheet.col(3).width = 4000   # Trạng thái
        
        # Viết tiêu đề cột (dời xuống 2 dòng)
        headers = ['STT', 'Họ và tên', 'Thời gian vào', 'Trạng thái']
        for col, header in enumerate(headers):
            worksheet.write(2, col, header, header_style)
        
        # Viết dữ liệu
        current_row = 3
        current_department = None
        current_parent_department = None
        stt_in_department = 0  # Biến đếm STT trong mỗi đơn vị
        
        for employee in employee_data:
            # Lấy thông tin từ dữ liệu đã được xử lý
            department_name = employee['department_id']
            parent_department_name = employee['parent_department']
            
            # Kiểm tra nếu đơn vị cha thay đổi
            if parent_department_name != current_parent_department:
                current_parent_department = parent_department_name
                # Chèn dòng tiêu đề đơn vị cha (nếu có)
                if parent_department_name:
                    worksheet.write_merge(current_row, current_row, 0, 3, f"ĐƠN VỊ: {parent_department_name}", parent_department_header_style)
                    current_row += 1
                # Reset current_department để force việc hiển thị đơn vị con
                current_department = None
            
            # Kiểm tra nếu đơn vị thay đổi
            if department_name != current_department:
                current_department = department_name
                # Chèn dòng tiêu đề đơn vị
                if parent_department_name:
                    # Nếu có đơn vị cha, hiển thị với indent
                    worksheet.write_merge(current_row, current_row, 0, 3, f"  • {current_department}", department_header_style)
                else:
                    # Nếu không có đơn vị cha, hiển thị bình thường
                    worksheet.write_merge(current_row, current_row, 0, 3, f"{current_department}", department_header_style)
                current_row += 1
                stt_in_department = 1  # Reset STT khi đổi đơn vị
            
            # Viết thông tin nhân viên
            worksheet.write(current_row, 0, stt_in_department, cell_style)     # STT trong đơn vị
            worksheet.write(current_row, 1, employee['name'], cell_style)                  # Họ và tên
            worksheet.write(current_row, 2, employee['check_in'] or '', cell_style)  # Thời gian vào
            
            # Xử lý trạng thái
            status_text = {
                'late': 'Muộn',
                'right_time': 'Đúng giờ',
                'time_off': 'Nghỉ phép',
                'business_trip': 'Đi công tác',
                'none': 'Chưa điểm danh'
            }.get(employee['status'], '')
            
            worksheet.write(current_row, 3, status_text, cell_style)
            current_row += 1
            stt_in_department += 1  # Tăng STT trong đơn vị
        
        # Lưu file tạm thời
        file_path = tempfile.mktemp(suffix='.xls')
        workbook.save(file_path)
        
        # Đọc file và chuyển thành base64
        with open(file_path, 'rb') as file:
            file_data = base64.b64encode(file.read())
            
        # Xóa file tạm
        os.unlink(file_path)
        

        filename = f'Bao_cao_ngay_{formatted_date}.xls'
        
        # Tạo attachment
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': file_data,
            'res_model': self._name,
            'res_id': 0,
            'mimetype': 'application/vnd.ms-excel'
        })
        
        # Trả về URL để download file
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    @api.model
    def get_current_department(self):
        """Lấy thông tin đơn vị của người dùng hiện tại"""
        employee = self.env.user.employee_id
        if not employee or not employee.department_id:
            return {'department': None}
            
        return {
            'department': {
                'id': employee.department_id.id,
                'name': employee.department_id.name
            }
        }

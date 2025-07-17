from odoo import http,fields
from odoo.http import request
import json
from requests.auth import HTTPDigestAuth
from datetime import datetime, timedelta
import requests
import base64
import io
import threading
def upload_image_to_zalo(access_token, byte_data):
    url = "https://openapi.zalo.me/v2.0/oa/upload/image"
    
    # Prepare the headers with access token
    headers = {
        "access_token": access_token
    }
    files = {
        'file': byte_data
    }

    # Make the POST request to upload the image
    response = requests.post(url, headers=headers, files=files)
    attachment_id = response.json()['data']['attachment_id']
    # Check the response status
    if response.status_code == 200:
        print("Image uploaded successfully.")
        return True,attachment_id
    else:
        print(f"Failed to upload image. Status code: {response.status_code}")
        return False,""
    
# def zalo_send_image(access_token,user_id,mess_text,attachment_id):
#     url = "https://openapi.zalo.me/v2.0/oa/message"
    
#     headers = {
#         "Content-Type": "application/json",
#         "access_token": access_token    
#               }
    
#     data = {
#         "recipient": {
#             "user_id": user_id
#         },
#         "message": {
#             "text": mess_text,
#             "attachment": {
#             "payload": {
#                 "elements": [
#                 {
#                     "media_type": "image",
#                     "attachment_id": attachment_id
#                 }
#                 ],
#                 "template_type": "media"
#             },
#             "type": "template"
#             }
#         }
#     }
#     response = requests.post(url, headers=headers, json=data)
#     print("zalo response",response.json(),response.status_code)
#     return response.status_code

# def send_check_in_zalo(access_token,byte_data,employee_zalo_user_id,employee_name,check_in_datetime):
#     upload_response = upload_image_to_zalo(access_token = access_token,
#                                         byte_data = byte_data
#                                         )
#     print('upload_response',upload_response)
#     if upload_response['error'] == 0: #Success
#         print('zalo_send_image')
#         zalo_send_image(access_token = access_token,
#                         attachment_id = upload_response['data']['attachment_id'],
#                         user_id = employee_zalo_user_id,
#                         mess_text = employee_name+" có mặt lúc "+check_in_datetime
#                         )
        
def send_check_in_zalo(access_token,employee_zalo_user_id,employee_name,employee_no,attachment_id,check_in_status,check_in_datetime):
    url = "https://openapi.zalo.me/v3.0/oa/message/transaction"
    
    headers = {
        "Content-Type": "application/json",
        "access_token": access_token    
              }
    
    # Xác định style và value dựa vào check_in_status
    if check_in_status == 'late':
        status_style = "red"
        status_value = "Đi muộn"
    elif check_in_status == 'right_time':
        status_style = "green"
        status_value = "Đúng giờ"
    else:
        status_style = "blue"
        status_value = "Chưa xác định"

    data = {
        "recipient": {
            "user_id": employee_zalo_user_id
        },
        "message": {
            "attachment": {
            "payload": {
                "buttons": [
                {
                    "payload": {
                    "phone_code": "84899093899"
                    },
                    "image_icon": "",
                    "title": "Hotline công ty",
                    "type": "oa.open.phone"
                }
                ],
                "elements": [
                {
                    "attachment_id": attachment_id,
                    "type": "banner"
                },
                {
                    "type": "header",
                    "align": "left",
                    "content": "Thông báo điểm danh"
                },
                {
                    "type": "text",
                    "align": "left",
                    "content": "Công Ty Dịch Vụ MobiFone Khu Vực 5 thông báo trạng thái điểm danh của anh/chị như sau:"
                },
                {
                    "type": "table",
                    "content": [
                        {
                            "value": employee_no,
                            "key": "Mã nhân viên"
                        },
                        {
                            "value": employee_name,
                            "key": "Tên nhân viên"
                        },
                        {
                            "value": check_in_datetime,
                            "key": "Thời gian"
                        },
                        {
                            "style": status_style,
                            "value": status_value,
                            "key": "Trạng thái"
                        }
                    ]
                },
                {
                    "type": "text",
                    "align": "center",
                    "content": "Chúc anh/chị có một ngày làm việc hiệu quả!"
                }
                ],
                "template_type": "transaction_internal",
                "language": "VI"
            },
            "type": "template"
            }
        }
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        print("zalo response",response.json(),response.status_code)
        return response.status_code
    except Exception as e:
        print('ERROR send_check_in_zalo',e)
        return 500
        

class HikvisionMinmoe(http.Controller):
    @http.route("/ISAPI",methods=['POST'], auth='public',csrf=False)
    def ISAPI(self, **kw):
        # print(kw)
        try:
            info_checkin = json.loads(kw['event_log'])

            if info_checkin['AccessControllerEvent']['subEventType']==75:
                image_checkin = kw['Picture']
                image_checkin_memory_file = io.BytesIO()
                image_checkin = image_checkin.save(image_checkin_memory_file)
                deviceName = info_checkin['AccessControllerEvent']['deviceName']
                employeeNoString = int(info_checkin['AccessControllerEvent']['employeeNoString'])
                serialNo = info_checkin['AccessControllerEvent']['serialNo']
                check_in_datetime = (datetime.fromisoformat(info_checkin["dateTime"]) - timedelta(hours=7)).replace(tzinfo=None)
                # employee_record = request.env['hr.employee'].sudo().search([('employee_id_hik','=',employeeNoString)],limit=1)
                employee_record = request.env['hr.employee'].sudo().browse(employeeNoString)
                if len(employee_record) > 0:
                    check_tyle, check_in_status = request.env['hr.attendance'].sudo().create_check_in_out(employee_id = employee_record.id,
                                                                                 check_in_time = check_in_datetime,
                                                                                 image_checkin =  base64.b64encode(image_checkin_memory_file.getvalue()).decode('utf-8'))

                    
                    if employee_record.zalo_user_id and employee_record.zalo_oa_access_token and check_tyle == 'check_in': 
                        check_in_datetime = datetime.fromisoformat(info_checkin["dateTime"]).strftime('%d/%m/%Y %H:%M:%S')
                        image_byte_data = image_checkin_memory_file.getvalue()
                        upload_success,attachment_id = upload_image_to_zalo(employee_record.zalo_oa_access_token,
                                                               image_byte_data)
                        if upload_success:
                            send_check_in_zalo(employee_record.zalo_oa_access_token,
                                            employee_record.zalo_user_id,
                                            employee_record.name,
                                            employee_record.id,
                                            attachment_id,
                                            check_in_status,
                                            check_in_datetime)

                        # t = threading.Thread(target = send_check_in_zalo, args = (employee_record.zalo_oa_access_token,
                        #                                                         # image_byte_data,
                        #                                                         employee_record.zalo_user_id,
                        #                                                         employee_record.name,
                        #                                                         employee_record.employee_id_hik,
                        #                                                         image_checkin_url,
                        #                                                         check_in_datetime,
                        #                                                         ))
                        # t.start()
   
                # print(info_checkin)

        except Exception as e:
            print('ERROR',e)
        return "OK"


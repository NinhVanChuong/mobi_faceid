from odoo import models, fields, api
import requests

class ZaloOA(models.Model):
    _name = 'zalo.oa'
    _description = 'Zalo office acount'

    name = fields.Char(string='Zalo OA name')
    access_token = fields.Char()
    refresh_token = fields.Char()
    secret_key = fields.Char()
    app_id = fields.Char()
    app_name = fields.Char()
    department_ids = fields.One2many('hr.department','zalo_oa_id')
    # employee_ids = fields.One2many('hr.employee','zalo_oa_id')

    def update_access_token(self):
        url = f"https://oauth.zaloapp.com/v4/oa/access_token?secret_key={self.secret_key}"

        payload = f'app_id={self.app_id}&refresh_token={self.refresh_token}&grant_type=refresh_token'
        headers = {
        'secret_key': self.secret_key,
        'Content-Type': 'application/x-www-form-urlencoded'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code == 200:
            self.access_token = response.json()['access_token']
            self.refresh_token = response.json()['refresh_token']
            return True
        else:
            print(response.json())
            return False

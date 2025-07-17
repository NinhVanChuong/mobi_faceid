from odoo import models, fields, api


class HikvisionMinmoe(models.Model):
    _name = 'hikvision.minmoe'
    _description = 'Hikvision Minmoe Device'

    name = fields.Char(string='Hikvision Minmoe Device name')
    _sql_constraints = [('unique_name','unique (name)','name must be unique')]

    username = fields.Char()
    password = fields.Char()
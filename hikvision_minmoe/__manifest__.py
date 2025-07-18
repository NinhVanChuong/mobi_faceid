# -*- coding: utf-8 -*-
{
    'name': "Hikvision_minmoe",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "AnhDaiDo",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr_attendance','advance_hr_attendance_dashboard', 'auth_ldap'],

    # always loaded
    'data': [
        'security/employee_department.xml',
        'security/ir.model.access.csv',
        'views/hr_attendance_views.xml',
        'views/hr_department_views.xml',
        'views/hr_employee_views.xml',
        'views/hr_attendance_shift_views.xml',
        'views/hr_attendance_shift_register_views.xml',
        'views/zalo_oa_views.xml',
        'data/hr_leave_type_data.xml',
        'data/zalo_oa_cron.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'license': 'LGPL-3',
}


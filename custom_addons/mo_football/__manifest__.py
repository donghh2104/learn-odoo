# -*- coding: utf-8 -*-
{
    'name': "mo_football",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose12
    """,

    'author': "Huu Dong 1",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    # any module necessary for this one to work correctly
    'depends': ['base'],

}

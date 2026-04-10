# -*- coding: utf-8 -*-
{
    'name': 'Quản lý Bất động sản',
    'version': '14.0.2.0.0',
    'summary': 'Quản lý tin đăng, lời đề nghị và giao dịch BĐS',
    'description': """
        Module Quản lý Bất động sản (Real Estate)
        =========================================
        Các tính năng chính:
        - Quản lý danh mục nhà đất, căn hộ
        - Theo dõi các lời đề nghị mua từ khách hàng
        - Quy trình bán hàng từ lúc đăng tin đến khi chốt giao dịch
        - Phân quyền nhân viên, kiểm toán viên và quản lý
        - Chatter/Activities, Cron automation, API JWT và báo cáo
    """,
    'author': 'Huu Dong',
    'website': 'https://github.com/donghh2104/learn-odoo',
    'category': 'Real Estate/Brokerage',
    'license': 'LGPL-3',
    'depends': ['base', 'web', 'mail'],
    'external_dependencies': {
        'python': ['jwt'],
    },
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/estate_sequence_data.xml',
        'data/estate_property_type_data.xml',
        'data/estate_cron.xml',
        'views/estate_property_tag_views.xml',
        'views/estate_property_type_views.xml',
        'views/estate_property_offer_views.xml',
        'views/estate_property_views.xml',
        'views/res_partner_views.xml',
        'wizards/estate_property_offer_wizard_views.xml',
        'views/assets.xml',
        'views/estate_menus.xml',
        'reports/estate_property_report.xml',
        'reports/estate_property_report_templates.xml',
    ],
    'demo': [
        'data/estate_demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

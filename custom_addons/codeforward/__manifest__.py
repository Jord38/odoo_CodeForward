# -*- coding: utf-8 -*-
{
    'name': "codeforward",

    'summary': "Module that implements an ftp interface with the purpose of synchronising two systems",

    'description': """
Long description of module's purpose
    """,

    'author': "Jord Duineveld",
    'website': "https://codeforward.nl",
    'license': 'LGPL-3',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/devices_view.xml',
        'views/content_view.xml',
        'views/views.xml',
        'views/res_config_settings_views.xml',
        'data/cron_data.xml',
    ],
    # only loaded in demonstration mode
    #'demo': [
    #    'demo/demo.xml',
    #],
}


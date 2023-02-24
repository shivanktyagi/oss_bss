# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2022 (https://www.in2ittech.com)
#
##############################################################################
{
    'name': 'OSS Odoo Debranding',
    'description': """
    	Odoo Color Change.

    """,
    'summary':'This Module is used Odoo Debranding',
    'version': '0.15.1',
    'license': 'LGPL-3',
    'category':'base',
    'website': 'https://www.in2ittech.com',
    'author': '[Pawan Kumar] In2IT Technologies.',
    'maintainer': 'Pawan Kumar',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_setting_debrand.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            '/odoo_debrand/static/src/scss/primary_variables_custom.scss',
        ],
        'web._assets_secondary_variablesweb.assets_backend': [
            '/odoo_debrand/static/src/scss/fields_extra_custom.scss',
        ],
        'web._assets_secondary_variables': [
            '/odoo_debrand/static/src/scss/secondary_variables.scss',
        ],
    },
    'images': [
        'static/description/icon.png'
    ],
    'installable': True
}

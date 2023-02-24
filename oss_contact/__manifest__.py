# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2022 (https://www.in2ittech.com)
#
##############################################################################
{
    'name': 'OSS Contact Creation',
    'description': """
    	As a CRM user I want to be able to create a Contact in Contact Management Module so
    	that the same can be viewed in Contact details list and utilized for Marketing, 
    	Sales and Customer Onboarding purposes.

    """,
    'summary':'This Module is used As a CRM user I want to be able to create a Contact in Contact Management Module.',
    'version': '0.15.1',
    'license': 'LGPL-3',
    'category':'base',
    'website': 'https://www.in2ittech.com',
    'author': '[Pawan Kumar] In2IT Technologies.',
    'maintainer': 'Pawan Kumar',
    'depends': ['base','contacts','sale_crm','base_geolocalize'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/mail_template_data.xml',
        'views/oss_partner_view.xml',
        'views/partner_inherit_site_view.xml',
        'wizard/create_table_dynamic_wizard.xml',
        'views/crm_configuration_view.xml',
        'views/crm_lead_capturing.xml',
        'demo/demo_data.xml',
    ],
    'images': [
        'static/description/icon.png'
    ],
    'installable': True
}

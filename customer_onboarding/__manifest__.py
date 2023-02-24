# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2022 (https://www.in2ittech.com)
#
##############################################################################
{
    'name': 'Customer Onboarding',
    'description': """
    - Partner Extension for OSS/BSS Customer Details
    """,
    'summary':'This Module is used to extend the functionality of res partner \
    module for add customer details.',
    'version': '0.15.1',
    'category':'base',
    'website': 'https://www.in2ittech.com',
    'author': 'In2IT Technologies.',
    'maintainer': 'Pawan Kumar',
    'depends': ['base','contacts','crm','sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/partner_onboarding_view.xml',
        'views/customer_requirement_view.xml',
    ],
    'images': [
        'static/description/icon.png'
    ],
    'installable': True
}

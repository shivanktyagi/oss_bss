# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2022 (https://www.in2ittech.com)
#
##############################################################################
{
    'name': 'OSS Product Catalog',
    'description': """
    	Add Product Features and Add Multiple devices as optional products

    """,
    'summary':'This Module is used Add Product features and add devices',
    'version': '0.15.1',
    'license': 'LGPL-3',
    'category':'base',
    'website': 'https://www.in2ittech.com',
    'author': '[Pawan Kumar] In2IT Technologies.',
    'maintainer': 'Pawan Kumar',
    'depends': ['sale_management', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_supported_devices_view.xml',
        'views/oss_product_display_views.xml'
        # 'views/product_category_listing_page_view.xml'
    ],
    'images': [
        'static/description/icon.png'
    ],
    'installable': True
}

# -*- coding: utf-8 -*-
{
    'name': 'Sale Custom',
    'summary': """Sale order and product template custom""",
    'version': '12.0.1.0.0',
    'description': """""",
    'author': 'Digital Assets',
    'website': 'http://www.digitalais.com',
    'category': 'Uncategorized',
    'depends': ['sale', 'sales_team'],
    'data': [
        'views/sale_order_view.xml',
        'security/ir.model.access.csv',
        'data/email_template.xml',
    ],
    'installable': True,

}

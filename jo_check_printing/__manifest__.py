# -*- coding: utf-8 -*-
{
    'name': 'Jordanian Checks Layout',
    'version': '1.0',
    'author': 'Digital Assets',
    'category': 'Accounting',
    'summary': 'Print JO Checks',
    'description': """This module allows to print your payments on pre-printed checks.""",
    'website': 'https://www.digitaiais.net',
    'depends': ['account_check_printing'],
    'data': [
        'data/jo_check_print.xml',
        'report/print_check.xml',
        'report/print_check_bottom.xml',
        'report/print_check_middle.xml',
        'report/print_check_top.xml',
    ],
    'installable': True,
    'auto_install': True,
}

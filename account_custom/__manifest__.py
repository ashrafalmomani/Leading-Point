# -*- coding: utf-8 -*-
{
    'name': 'Account Custom',
    'summary': """Add cheque details on the payment voucher""",
    'version': '12.0.1.0.0',
    'description': """Add cheque number and bank name""",
    'author': 'Digital Assets',
    'website': 'http://www.digitalais.com',
    'category': 'Uncategorized',
    'depends': ['base', 'account', 'account_check_printing'],
    'data': [
        'views/account_payment.xml',
    ],
    'installable': True,

}

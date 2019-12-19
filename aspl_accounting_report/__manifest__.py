# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

{
    'name': "Accounting Report",
    'version': '1.0',
    'category': 'Accounting',
    'description': """
        Use can print all accouting reports in PDF and XLS format
    """,
    'author': 'Acespritech Solutions Pvt. Ltd',
    'website': 'http://www.acespritech.com',
    'summary': '',
    'price': '30.00',
    'currency': 'EUR',
    'depends': ['base', 'account'],
    'images': ['static/description/report_menu.png'],
    'data': [
        'security/ir.model.access.csv',
        'report/account_report.xml',
        'report/customer_vendors_receivables.xml',
        'views/tax_report_template.xml',
        'views/trial_balance_template.xml',
        'views/aged_payble_template.xml',
        'views/aged_receivable_template.xml',
        'views/partner_ledger_template.xml',
        'wizard/tax_report_wiz_view.xml',
        'wizard/aged_payble_view.xml',
        'wizard/trial_balance_wiz_view.xml',
        'wizard/aged_receivable_view.xml',
        'wizard/account_report_partner_ledger_view.xml',
        'wizard/customer_vendor_receivable.xml',
        'views/account_pdf_reports.xml',
        'wizard/profit_and_loss.xml',
        'wizard/balance_sheet.xml',
        'views/general_ledger_template.xml',
        'wizard/general_ledger_wiz_view.xml',
        'report/report_financial.xml',
    ],
    'qweb': [],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

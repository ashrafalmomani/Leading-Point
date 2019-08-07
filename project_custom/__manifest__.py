# -*- coding: utf-8 -*-

{
    'name': 'Project Custom',
    'version': '12.0.1.0.0',
    'author': 'Digital Assets',
    'website': 'http://www.digitalais.com',
    'category': 'Project Management',
    'depends': ['project'],
    'data': [
        'security/ir.model.access.csv',
        'views/project_view.xml',
        'views/account_analytic_line.xml',
    ],
    'installable': True,
}

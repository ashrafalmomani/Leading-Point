# -*- coding: utf-8 -*-

{
    'name': 'Disable Create & Create and Edit',
    'version': '11.0.1.0.0',
    'category': 'Tools',
    'license': 'AGPL-3',
    'summary': 'Disable Create & Create and Edit on all objects',
    'description': """
Disables Create and Edit from all the models and fields
=========================================================
Disable quick create on all objects of Odoo.

    """,
    'author': 'ME',
    'website': '',
    'depends': ['base'],
    'installable': True,
    'data': ['views/many2one_view.xml',]
}

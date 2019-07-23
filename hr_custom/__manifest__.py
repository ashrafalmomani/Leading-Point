# -*- coding: utf-8 -*-
{
    'name': 'HR Custom',
    'summary': """Human Resource customization""",
    'version': '12.0.1.0.0',
    'description': """Human Resource customization""",
    'author': 'Digital Assets',
    'website': 'http://www.digitalais.com',
    'category': 'Uncategorized',
    'depends': ['hr', 'project', 'project_team'],
    'data': [
        'views/hr_employee_view.xml',
        'views/hr_hotels_view.xml',
        'views/hr_tickets_view.xml',
        'views/hr_travel_view.xml',
        'views/hr_visas_view.xml',
        'views/hr_leave_view.xml',
        'data/cron.xml',
        'data/data_tags.xml',
        'data/sequence.xml',
        'data/employee_rule.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,

}

# -*- coding: utf-8 -*-
{
    'name': 'HR Custom',
    'summary': """Human Resource customization""",
    'version': '12.0.1.0.0',
    'description': """Human Resource customization""",
    'author': 'Digital Assets',
    'website': 'http://www.digitalais.com',
    'category': 'Human Resource',
    'depends': ['hr', 'project', 'project_custom', 'om_account_asset', 'crm_custom', 'survey', 'hr_timesheet'],
    'data': [
        'views/hr_employee_view.xml',
        'views/asset_management_view.xml',
        'views/hr_travel_view.xml',
        'views/hr_awarded_days.xml',
        'views/hr_hotels_view.xml',
        'views/hr_tickets_view.xml',
        'views/hr_visas_view.xml',
        'views/hr_leave_view.xml',
        'views/hr_payroll_view.xml',
        'views/hr_appraisal_view.xml',
        'views/hr_expense_view.xml',
        'wizard/run_per_diem_views.xml',
        'data/cron.xml',
        'data/data_tags.xml',
        'data/sequence.xml',
        'data/employee_rule.xml',
        'data/mail_activity.xml',
        'data/email_template.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,

}

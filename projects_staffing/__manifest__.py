{
    'name': 'Project Staffing',
    'version': '12.0.1.0.0',
    'category': 'Human Resource',
    'author': 'Digital Asset Team',
    "website": "https://digitalais.com",
    'depends': ['hr', 'project', 'project_custom', 'web_gantt_native'],
    'data': [
             'views/sequence.xml',
             'views/staffing_request_view.xml',
             'data/cron.xml',
             'data/email_template.xml',
             'security/ir.model.access.csv',
             ],
    'installable': True,
    'application': False,
    'auto_install': False,
}

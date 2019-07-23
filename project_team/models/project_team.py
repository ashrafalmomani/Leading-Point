
from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    members = fields.Many2many('hr.employee', 'project_employee_rel', 'project_id',
                               'employee_id', 'Project Members', help="""Project's
                               members are users who can have an access to
                               the tasks related to this project.""")

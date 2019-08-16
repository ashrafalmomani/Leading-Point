# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProjectStatus(models.Model):
    _name = "project.status"
    _description = "Project Status"

    name = fields.Char(required=True)
    close_stage = fields.Boolean('Is Close Stage?')


class ProjectProject(models.Model):
    _inherit = 'project.project'

    stage_id = fields.Many2one('project.status', string='State')
    members = fields.Many2many('hr.employee', 'project_employee_rel', 'project_id',
                               'employee_id', 'Project Members', help="""Project's
                               members are users who can have an access to the tasks related to this project.""")

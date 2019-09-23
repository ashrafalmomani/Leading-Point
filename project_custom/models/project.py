# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProjectStatus(models.Model):
    _name = "project.status"
    _description = "Project Status"

    name = fields.Char(required=True)
    close_stage = fields.Boolean('Is Close Stage?')


class ProjectProject(models.Model):
    _inherit = 'project.project'

    @api.model
    def _get_default_stage_id(self):
        return self.env['project.status'].search([], order="id asc", limit=1)

    stage_id = fields.Many2one('project.status', string='Stage', ondelete='restrict', track_visibility='onchange',
                               default=_get_default_stage_id, copy=False)
    members = fields.Many2many('hr.employee', 'project_employee_rel', 'project_id',
                               'employee_id', 'Project Members', help="""Project's
                               members are users who can have an access to the tasks related to this project.""")


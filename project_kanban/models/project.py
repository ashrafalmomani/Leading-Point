# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProjectStatus(models.Model):
    _name = "project.status"
    _description = "Project Status"

    name = fields.Char(required=True)


class ProjectProject(models.Model):
    _inherit = 'project.project'

    stage_id = fields.Many2one('project.status', string='State')

# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class CrmAndSales(models.Model):
    _inherit = "crm.lead"

    team_member = fields.Many2many('hr.employee', string='Team Member')
    owner = fields.Many2one('hr.employee', string='Owner')

    @api.multi
    def projects_opportunity(self):
        return {
            'name': _('Projects'),
            'domain': [('opportunity_id', 'in', [self.id])],
            # 'context': {'default_opportunity_id': 'active_id'},
            'res_model': 'project.project',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'views': [(self.env.ref('project.view_project_kanban').id, 'kanban')],
            'view_type': 'kanban',
            'view_mode': 'kanban,',
            'target': 'current'}


class ResPartner(models.Model):
    _inherit = "res.partner"

    industry = fields.Many2one('res.partner.industry', string='Industry')


class ProjectsProjects(models.Model):
    _inherit = "project.project"

    opportunity_id = fields.Many2one('crm.lead', string='Opportunity')



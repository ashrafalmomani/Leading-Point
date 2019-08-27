# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class CrmAndSales(models.Model):
    _inherit = "crm.lead"

    team_member = fields.Many2many('hr.employee', string='Team Members', track_visibility='always')
    owner = fields.Many2one('hr.employee', string='Owner', track_visibility='always')
    analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account', track_visibility='always')
    document = fields.Char(string='Document', track_visibility='always')
    stakeholder_ids = fields.Many2many('res.partner', string='Stakeholders', track_visibility='always')

    @api.model
    def create(self, vals):
        analytic_id = self.env['account.analytic.account'].create({
            'name': 'Opportunity (%s)' % vals.get('name'),
            'partner_id': vals.get('partner_id'),
            'active': True,
        })
        vals.update({'analytic_id': analytic_id.id})
        return super(CrmAndSales, self).create(vals)


class ResPartner(models.Model):
    _inherit = "res.partner"

    industry = fields.Many2one('res.partner.industry', string='Industry', track_visibility='always')
    linked_in = fields.Char(string='LinkedIn', track_visibility='always')
    relationship = fields.Selection([('sale_lead', 'Sales Lead'),
                                     ('dev_lead', 'BizDev Lead'),
                                     ('prospect', 'Prospect'),
                                     ('customer', 'Customer'),
                                     ('partner', 'Partner'),
                                     ('competitor', 'Competitor'),
                                     ('vendor', 'Vendor'),
                                     ('employee', 'Employee')], string="Relationship", default='sale_lead', track_visibility='always')

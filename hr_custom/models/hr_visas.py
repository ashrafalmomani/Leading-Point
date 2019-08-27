# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HREmployeeVisas(models.Model):
    _name = "hr.visas"
    _description = 'Visas'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'travel_id'

    travel_id = fields.Many2one('hr.travel', string='Travel', track_visibility='always', domain="[('state', '=', 'hr_approved'), ('visa_required', '=', True)]")
    valid_form = fields.Date(string='Valid From', track_visibility='always')
    valid_till = fields.Date(string='Valid Till', track_visibility='always')
    multiple_entry = fields.Boolean(string='Is Multiple Entry', track_visibility='always')
    visa = fields.Binary(string='UPLOAD YOUR FILE', track_visibility='always')
    cost = fields.Float(string='Cost', track_visibility='always')
    state = fields.Selection([('draft', 'Draft'), ('pending', 'Pending'), ('applied', 'Applied'),
                              ('issued', 'Issued'), ('rejected', 'Rejected'), ('cancelled', 'Cancelled')],
                             default='draft', store=True, track_visibility='always')

    @api.multi
    def action_visa_applied(self):
        self.state = 'applied'

    @api.multi
    def action_visa_issued(self):
        if self.travel_id.reason_for_travel in ('project', 'business_dev'):
            for rec in self.travel_id.percentage_ids:
                self.env['account.analytic.line'].create({
                    'name': "Visa for (%s) Travel" % self.travel_id.name,
                    'project_id': rec.project_id.id or False,
                    'account_id': rec.project_id.analytic_account_id.id or rec.lead_id.analytic_id.id,
                    'amount': self.cost * (rec.percentage / 100),
                    'unit_amount': 1,
                    'user_id': self.travel_id.employee.user_id.id,
                    'date': fields.Date.today(),
                    'partner_id': self.travel_id.employee.user_id.partner_id.id,
                })
        else:
            self.env['account.analytic.line'].create({
                'name': "Visa for (%s) Travel" % self.travel_id.name,
                'account_id': self.travel_id.analytic_id.id,
                'amount': self.cost,
                'unit_amount': 1,
                'user_id': self.travel_id.employee.user_id.id,
                'date': fields.Date.today(),
                'partner_id': self.travel_id.employee.user_id.partner_id.id,
            })
        self.state = 'issued'

    @api.multi
    def action_visa_rejected(self):
        self.state = 'rejected'

    @api.multi
    def action_cancel(self):
        self.state = 'cancelled'

# -*- coding: utf-8 -*-


from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AccountAnalyticLine(models.Model):
    _name = 'account.analytic.line'
    _inherit = ['account.analytic.line', 'mail.thread', 'mail.activity.mixin', 'portal.mixin']

    employee_id = fields.Many2one('hr.employee', string='Employee')
    name = fields.Char(string='Description', track_visibility='always')
    lead_id = fields.Many2one('crm.lead', string='Lead/Opportunity', track_visibility='always')
    work_place = fields.Selection([('inside', 'Onsite'), ('outside', 'Offsite')], string="Work Place", track_visibility='always')
    reason = fields.Text('Reject Reason', track_visibility='always')
    type_id = fields.Selection([('project', 'Project'), ('opportunity', 'Opportunity'),
                                ('Travel', 'travel'), ('Leave', 'Leave'), ('unassigned', 'Unassigned')], string="Type", track_visibility='always')
    state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted'), ('approved', 'Approved'),
                              ('rejected', 'Rejected')], default='draft', track_visibility='always')

    @api.multi
    def button_done(self):
        self.state = 'done'

    @api.multi
    def button_submitted(self):
        self.state = 'submitted'

    @api.multi
    def button_approved(self):
        self.state = 'approved'

    @api.multi
    def button_rejected(self):
        if not self.reason:
            raise ValidationError('You must insert the reject reason!')
        else:
            self.state = 'rejected'

    @api.onchange('project_id')
    def _onchange_project_id(self):
        if self.project_id:
            self.account_id = self.project_id.analytic_account_id.id

    @api.onchange('lead_id')
    def _onchange_lead_id(self):
        if self.lead_id:
            self.account_id = self.lead_id.analytic_id.id

    @api.onchange('project_id')
    def _onchange_description_project(self):
        if self.project_id:
            self.name = 'Project- %s ' % self.project_id.name

    @api.onchange('lead_id')
    def _onchange_description_lead(self):
        if self.lead_id:
            self.name = 'Lead- %s ' % self.lead_id.name

# -*- coding: utf-8 -*-


from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AccountAnalyticLine(models.Model):
    _name = 'account.analytic.line'
    _inherit = ['account.analytic.line', 'mail.thread', 'mail.activity.mixin', 'portal.mixin']

    name = fields.Char('Description', attrs="{'required': [('unassigned', '=', True)]}" )
    lead_id = fields.Many2one('crm.lead', string='Lead/Opportunity')
    work_place = fields.Selection([('inside', 'Inside'), ('outside', 'Outside')], string="Work Place")
    reason = fields.Text('Reject Reason')
    type_id = fields.Selection([('project', 'Project'), ('opportunity', 'Opportunity'),
                                ('Travel', 'travel'), ('Leave', 'Leave'), ('unassigned', 'Unassigned')], string="Type")
    state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted'), ('approved', 'Approved'),
                              ('rejected', 'Rejected')], default='draft')

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

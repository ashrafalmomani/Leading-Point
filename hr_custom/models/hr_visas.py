# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HREmployeeVisas(models.Model):
    _name = "hr.visas"
    _description = 'Visas'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'travel_visas'

    travel_visas = fields.Many2one('hr.travel', string='Travel')
    valid_form = fields.Date(string='Valid From')
    valid_till = fields.Date(string='Valid Till')
    multiple_entry = fields.Boolean(string='Is Multiple Entry')
    visa = fields.Binary(string='UPLOAD YOUR FILE')
    cost = fields.Float(string='Cost')
    visa_id = fields.Many2one('hr.travel', string='Visas')
    state = fields.Selection([('draft', 'Draft'),
                              ('pending', 'Pending'),
                              ('applied', 'Applied'),
                              ('issued', 'Issued'),
                              ('rejected', 'Rejected')], default='draft', store=True)

    @api.multi
    def action_visa_applied(self):
        self.state = 'applied'

    @api.multi
    def action_visa_issued(self):
        self.state = 'issued'

    @api.multi
    def action_visa_rejected(self):
        self.state = 'rejected'

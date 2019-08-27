# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions


class HREmployeeHotels(models.Model):
    _name = "hr.hotels"
    _description = 'Hotels'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'travel_id'

    hotel_name = fields.Char(string='Hotel Name', track_visibility='always')
    reservation_num = fields.Char(string='Reservation Number', track_visibility='always')
    travel_id = fields.Many2one('hr.travel', string='Travel', track_visibility='always', domain="[('state', '=', 'hr_approved'), ('hotel_required', '=', True)]")
    check_in = fields.Date(string='Check In', track_visibility='always')
    check_out = fields.Date(string='Check Out', track_visibility='always')
    cost = fields.Float(string='Cost', track_visibility='always')
    reservation = fields.Binary(string='UPLOAD YOUR FILE', track_visibility='always')
    state = fields.Selection([('draft', 'Draft'), ('reserved', 'Reserved'), ('cancelled', 'Cancelled')],
                             default='draft', store=True, track_visibility='always')

    @api.constrains('check_in', 'check_out')
    def check_reservation_date(self):
        if self.check_in < self.travel_id.from_date or self.check_out > self.travel_id.to_date:
            raise exceptions.ValidationError(_("The reservation date must belong to the travel date"))

    @api.constrains('cost')
    def check_cost(self):
        if self.cost <= 0.0:
            raise exceptions.ValidationError(_("The reservation cost must be greater than 0.0"))

    @api.multi
    def action_reserved(self):
        if self.travel_id.reason_for_travel in ('project', 'business_dev'):
            for rec in self.travel_id.percentage_ids:
                self.env['account.analytic.line'].create({
                    'name': "Hotel for (%s) Travel" % self.travel_id.name,
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
                'name': "Hotel for (%s) Travel" % self.travel_id.name,
                'account_id': self.travel_id.analytic_id.id,
                'amount': self.cost,
                'unit_amount': 1,
                'user_id': self.travel_id.employee.user_id.id,
                'date': fields.Date.today(),
                'partner_id': self.travel_id.employee.user_id.partner_id.id,
            })
        self.state = 'reserved'

    @api.multi
    def action_cancel(self):
        self.state = 'cancelled'

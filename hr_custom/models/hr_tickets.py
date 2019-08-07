# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions
from datetime import timedelta


class HREmployeeTickets(models.Model):
    _name = "hr.tickets"
    _description = 'Tickets'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'travel_id'

    travel_id = fields.Many2one('hr.travel', string='Travel', track_visibility='always', domain="[('state', '=', 'hr_approved'), ('trip_status', 'in', ['preparing', 'ready', 'open'])]")
    ticket_num = fields.Char(string='Ticket Number', track_visibility='always')
    departure_date = fields.Datetime(string='Departure Date', track_visibility='always')
    return_date = fields.Datetime(string='Return Date', track_visibility='always')
    price = fields.Float(string='Price', track_visibility='always')
    ticket = fields.Binary(string='UPLOAD YOUR FILE', track_visibility='always')
    notes = fields.Char(string='Notes', track_visibility='always')
    type = fields.Selection([('new_ticket', 'New Ticket'), ('change_reservation', 'Change Reservation')], string='Type', track_visibility='always')
    airline = fields.Selection([('emirates', 'Emirates Airlines'), ('saudi', 'Saudi Airlines'),
                                ('royal', 'Royal Jordanian'), ('qatar', 'Qatar Airways'), ('oman', 'Oman Air'),
                                ('gulf', 'Gulf Air')], string='Airline', track_visibility='always')
    state = fields.Selection([('draft', 'Draft'), ('issued', 'Issued'), ('cancelled', 'Cancelled')],
                             default='draft', store=True, track_visibility='always')

    @api.constrains('price')
    def check_price(self):
        if self.price <= 0.0:
            raise exceptions.ValidationError(_("The ticket price must be greater than 0.0"))

    @api.multi
    def action_cancel(self):
        self.state = 'cancelled'

    @api.multi
    def travel_update_ticket_status(self):
        self.travel_id.write({'from_date': self.departure_date.date(), 'to_date': self.return_date.date()})
        if self.travel_id.reason_for_travel in ('project', 'business_dev'):
            for rec in self.travel_id.percentage_ids:
                self.env['account.analytic.line'].create({
                    'name': "Ticket for (%s) Travel" % self.travel_id.name,
                    'project_id': rec.project_id.id or False,
                    'account_id': rec.project_id.analytic_account_id.id or rec.lead_id.analytic_id.id,
                    'unit_amount': self.price * (rec.percentage / 100),
                    'user_id': self.travel_id.employee.user_id.id,
                    'date': fields.Date.today(),
                    'employee_id': self.travel_id.employee.id,
                })
        else:
            self.env['account.analytic.line'].create({
                'name': "Ticket for (%s) Travel" % self.travel_id.name,
                'account_id': self.travel_id.analytic_id.id,
                'unit_amount': self.price,
                'user_id': self.travel_id.employee.user_id.id,
                'date': fields.Date.today(),
                'employee_id': self.travel_id.employee.id,
            })
        self.state = 'issued'

    @api.multi
    def _check_ticket_departure_date(self):
        tickets = self.env['hr.tickets'].search([('state', '=', 'issued')])
        for ticket in tickets:
            date = ticket.departure_date.date() - timedelta(days=1)
            user_id = self.env['res.users'].search([('groups_id', 'in', self.env.ref('hr.group_hr_manager').id)], limit=1, order="id desc")
            if date == fields.Date.today():
                notification = {
                    'activity_type_id': self.env.ref('hr_custom.mail_activity_ticket_notification').id,
                    'res_id': ticket.id,
                    'res_model_id': self.env['ir.model'].search([('model', '=', 'hr.tickets')], limit=1).id,
                    'icon': 'fa-pencil-square-o',
                    'date_deadline': fields.Datetime.now(),
                    'user_id': user_id.id,
                    'note': 'Tomorrow his travel for ('+ ticket.travel_id.name +') please, pay attention if there is a change in ticket information'
                }
                self.env['mail.activity'].create(notification)

# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HREmployeeTickets(models.Model):
    _name = "hr.tickets"
    _description = 'Tickets'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'ticket_num'

    travel_ticket = fields.Many2one('hr.travel', string='Travel')
    ticket_num = fields.Char(string='Ticket Number')
    departure_date = fields.Datetime(string='Departure Date')
    return_date = fields.Datetime(string='Return Date')
    price = fields.Float(string='Price')
    ticket = fields.Binary(string='UPLOAD YOUR FILE')
    notes = fields.Char(string='Notes')
    tickets_id = fields.Many2one('hr.travel', string='Tickets')
    state = fields.Selection([('draft', 'Draft'),
                              ('pending', 'Pending'),
                              ('issued', 'Issued'),
                              ('cancelled', 'Cancelled')], default='draft', store=True)

    airline = fields.Selection([('emirates', 'Emirates Airlines'),
                                ('saudi', 'Saudi Airlines'),
                                ('royal', 'Royal Jordanian'),
                                ('qatar', 'Qatar Airways'),
                                ('oman', 'Oman Air'),
                                ('gulf', 'Gulf Air')], string='Airline')

    type = fields.Selection([('new_ticket', 'New Ticket'),
                             ('change_reservation', 'Change Reservation')], string='Type')

    @api.multi
    def action_cancel(self):
        self.state = 'cancelled'

    @api.multi
    def action_issued(self):
        self.state = 'issued'

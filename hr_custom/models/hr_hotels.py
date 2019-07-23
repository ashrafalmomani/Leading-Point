# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HREmployeeHotels(models.Model):
    _name = "hr.hotels"
    _description = 'Hotels'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'reservation_num'

    travel_hotel = fields.Many2one('hr.travel', string='Travel')
    hotel_name = fields.Char(string='Hotel Name')
    reservation_num = fields.Char(string='Reservation Number')
    check_in = fields.Date(string='Check In')
    check_out = fields.Date(string='Check Out')
    cost = fields.Float(string='Cost')
    reservation = fields.Binary(string='UPLOAD YOUR FILE')
    hotel_id = fields.Many2one('hr.travel', string='Hotels')
    state = fields.Selection([('draft', 'Draft'),
                              ('pending', 'Pending'),
                              ('reserved', 'Reserved')], default='draft', store=True)

    @api.multi
    def action_reserved(self):
        self.state = 'reserved'

# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions
from datetime import timedelta
from odoo.exceptions import ValidationError


class HREmployeeTickets(models.Model):
    _name = "hr.tickets"
    _description = 'Tickets'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'travel_id'

    @api.model
    def _default_officer_user_id(self):
        return self.env['res.users'].search([('groups_id', 'in', self.env.ref('hr_custom.group_ticket_officer').id)],
                                            limit=1,
                                            order="id desc")

    def _default_manager_id(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])

    travel_id = fields.Many2one('hr.travel', string='Travel', track_visibility='always', domain="[('state', '=', 'hr_approved'), ('trip_status', 'in', ['preparing', 'ready', 'open'])]")
    ticket_num = fields.Char(string='Ticket Number', track_visibility='always')
    departure_date = fields.Datetime(string='Departure Date', track_visibility='always')
    return_date = fields.Datetime(string='Return Date', track_visibility='always')
    new_departure_date = fields.Datetime(string='New Departure Date', track_visibility='always')
    new_return_date = fields.Datetime(string='New Return Date', track_visibility='always')
    cost = fields.Float(string='Cost', track_visibility='always')
    ticket = fields.Binary(string='UPLOAD YOUR FILE', track_visibility='always')
    notes = fields.Char(string='Notes', track_visibility='always')
    reject_des = fields.Text(string='Reject Reason')
    reservation_ids = fields.One2many('hr.change.ticket', 'ticket_id', string='Change Ticket',
                                      track_visibility='always')
    is_confirm_true = fields.Boolean(string='True', default=False)
    officer_user_id = fields.Many2one('res.users', default=_default_officer_user_id)
    project_manager = fields.Many2one('hr.employee', string='Project Manager', default=_default_manager_id,
                                      track_visibility='always')
    airline = fields.Selection([('emirates', 'Emirates Airlines'), ('saudi', 'Saudi Airlines'),
                                ('royal', 'Royal Jordanian'), ('qatar', 'Qatar Airways'), ('oman', 'Oman Air'),
                                ('gulf', 'Gulf Air')], string='Airline', track_visibility='always')
    state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted'), ('issued', 'Issued'), ('cancelled', 'Cancelled')],
                             default='draft', store=True, track_visibility='always')


    @api.onchange('departure_date', 'return_date')
    def _onchange_new_departure_and_return(self):
        if self.departure_date:
            self.new_departure_date = self.departure_date
        if self.return_date:
            self.new_return_date = self.return_date

    @api.multi
    def action_submitted(self):
        notification = {
            'activity_type_id': self.env.ref('hr_custom.notification_after_ticket_submitted').id,
            'res_id': self.id,
            'res_model_id': self.env['ir.model'].search([('model', '=', 'hr.tickets')], limit=1).id,
            'icon': 'fa-pencil-square-o',
            'date_deadline': fields.Date.today(),
            'user_id': self.officer_user_id.id,
            'note': 'Request For Ticket'
        }
        self.env['mail.activity'].create(notification)

        template_id = self.env.ref('hr_custom.email_after_ticket_submitted')
        composer = self.env['mail.compose.message'].sudo().with_context({
            'default_composition_mode': 'mass_mail',
            'default_notify': False,
            'default_model': 'hr.tickets',
            'default_res_id': self.id,
            'default_template_id': template_id.id,
        }).create({})
        values = composer.onchange_template_id(template_id.id, 'mass_mail', 'hr.tickets', self.id)['value']
        composer.write(values)
        composer.send_mail()

        self.state = 'submitted'


    @api.multi
    def action_ticket_issued(self):
        self.travel_id.write({'from_date': self.new_departure_date.date(), 'to_date': self.new_return_date.date()})
        if self.travel_id.reason_for_travel in ('project', 'business_dev'):
            for rec in self.travel_id.percentage_ids:
                self.env['account.analytic.line'].create({
                    'name': "Ticket for (%s) Travel" % self.travel_id.name,
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
                'name': "Ticket for (%s) Travel" % self.travel_id.name,
                'account_id': self.travel_id.analytic_id.id,
                'amount': self.cost,
                'unit_amount': 1,
                'user_id': self.travel_id.employee.user_id.id,
                'date': fields.Date.today(),
                'partner_id': self.travel_id.employee.user_id.partner_id.id,
            })

        notification = {
            'activity_type_id': self.env.ref('hr_custom.notification_after_ticket_approved').id,
            'res_id': self.id,
            'res_model_id': self.env['ir.model'].search([('model', '=', 'hr.tickets')], limit=1).id,
            'icon': 'fa-pencil-square-o',
            'date_deadline': fields.Date.today(),
            'user_id': self.project_manager.id,
            'note': 'The request for ticket is approved'
        }
        self.env['mail.activity'].create(notification)

        template_id = self.env.ref('hr_custom.email_after_ticket_approved')
        composer = self.env['mail.compose.message'].sudo().with_context({
            'default_composition_mode': 'mass_mail',
            'default_notify': False,
            'default_model': 'hr.tickets',
            'default_res_id': self.id,
            'default_template_id': template_id.id,
        }).create({})
        values = composer.onchange_template_id(template_id.id, 'mass_mail', 'hr.tickets', self.id)['value']
        composer.write(values)
        composer.send_mail()

        self.state = 'issued'


    @api.multi
    def action_cancel(self):
        self.state = 'cancelled'


    @api.multi
    def _check_ticket_departure_date(self):
        tickets = self.env['hr.tickets'].search([('state', '=', 'issued')])
        for ticket in tickets:
            date = ticket.new_departure_date.date() - timedelta(days=1)
            user_id = self.env['res.users'].search([('groups_id', 'in', self.env.ref('hr.group_hr_manager').id)], limit=1, order="id desc")
            if date == fields.Date.today():
                notification = {
                    'activity_type_id': self.env.ref('hr_custom.mail_activity_ticket_notification').id,
                    'res_id': ticket.id,
                    'res_model_id': self.env['ir.model'].search([('model', '=', 'hr.tickets')], limit=1).id,
                    'icon': 'fa-pencil-square-o',
                    'date_deadline': fields.Datetime.now(),
                    'user_id': user_id.id,
                    'note': 'Tomorrow the employee will travel ('+ ticket.travel_id.name +') please, pay attention if there is a change in ticket information'
                }
                self.env['mail.activity'].create(notification)


class HREmployeeChangeTicket(models.Model):
    _name = "hr.change.ticket"
    _description = 'Change Tickets'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'ticket_id'

    @api.model
    def _default_officer_user_id(self):
        return self.env['res.users'].search([('groups_id', 'in', self.env.ref('hr_custom.group_ticket_officer').id)],
                                            limit=1,
                                            order="id desc")

    def _default_manager_id(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])

    ticket_id = fields.Many2one('hr.tickets', string='Ticket', track_visibility='always')
    type = fields.Selection([('departure_and_return', 'Departure/Return Date'), ('return', 'Return Date'), ('open_return', 'Open Return Date')], string='Type', track_visibility='always')
    departure_date = fields.Datetime(string='Departure Date', track_visibility='always')
    return_date = fields.Datetime(string='Return Date', track_visibility='always')
    cost = fields.Float(string='Cost', track_visibility='always')
    officer_user_id = fields.Many2one('res.users', default=_default_officer_user_id)
    notes = fields.Char(string='Notes', track_visibility='always')
    project_manager = fields.Many2one('hr.employee', string='Project Manager', default=_default_manager_id,
                                      track_visibility='always')
    state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted'), ('issued', 'Issued'), ('cancelled', 'Cancelled')],
                             default='draft', store=True, track_visibility='always')

    @api.multi
    def action_submitted(self):
        if fields.Date.today() > self.ticket_id.new_departure_date.date() and self.type == 'departure_and_return':
            raise exceptions.ValidationError(_("You cannot change the departure date because he has already traveled"))
        notification = {
            'activity_type_id': self.env.ref('hr_custom.notification_after_change_ticket_submitted').id,
            'res_id': self.id,
            'res_model_id': self.env['ir.model'].search([('model', '=', 'hr.change.ticket')], limit=1).id,
            'icon': 'fa-pencil-square-o',
            'date_deadline': fields.Date.today(),
            'user_id': self.officer_user_id.id,
            'note': 'Request For Change Ticket'
        }
        self.env['mail.activity'].create(notification)

        template_id = self.env.ref('hr_custom.email_after_change_ticket_submitted')
        composer = self.env['mail.compose.message'].sudo().with_context({
            'default_composition_mode': 'mass_mail',
            'default_notify': False,
            'default_model': 'hr.change.ticket',
            'default_res_id': self.id,
            'default_template_id': template_id.id,
        }).create({})
        values = composer.onchange_template_id(template_id.id, 'mass_mail', 'hr.change.ticket', self.id)['value']
        composer.write(values)
        composer.send_mail()

        self.state = 'submitted'

    @api.multi
    def action_ticket_issued(self):
        if self.type == 'departure_and_return':
            self.ticket_id.write({'new_departure_date': self.departure_date.date(), 'new_return_date': self.return_date.date()})
            self.ticket_id.travel_id.write({'from_date': self.departure_date.date(), 'to_date': self.return_date.date()})
        elif self.type == 'return':
            self.ticket_id.write({'new_return_date': self.return_date.date()})
            self.ticket_id.travel_id.write({'to_date': self.return_date.date()})
        elif self.type == 'open_return':
            self.ticket_id.write({'new_return_date': False})
            self.ticket_id.travel_id.write({'to_date': False})
        if self.ticket_id.travel_id.reason_for_travel in ('project', 'business_dev'):
            for rec in self.ticket_id.travel_id.percentage_ids:
                self.env['account.analytic.line'].create({
                    'name': "Ticket for (%s) Travel" % self.ticket_id.travel_id.name,
                    'project_id': rec.project_id.id or False,
                    'account_id': rec.project_id.analytic_account_id.id or rec.lead_id.analytic_id.id,
                    'amount': self.cost * (rec.percentage / 100),
                    'unit_amount': 1,
                    'user_id': self.ticket_id.travel_id.employee.user_id.id,
                    'date': fields.Date.today(),
                    'partner_id': self.ticket_id.travel_id.employee.user_id.partner_id.id,
                })
        else:
            self.env['account.analytic.line'].create({
                'name': "Ticket for (%s) Travel" % self.ticket_id.travel_id.name,
                'account_id': self.ticket_id.travel_id.analytic_id.id,
                'amount': self.cost,
                'unit_amount': 1,
                'user_id': self.ticket_id.travel_id.employee.user_id.id,
                'date': fields.Date.today(),
                'partner_id': self.ticket_id.travel_id.employee.user_id.partner_id.id,
            })

        notification = {
            'activity_type_id': self.env.ref('hr_custom.notification_after_change_ticket_approved').id,
            'res_id': self.id,
            'res_model_id': self.env['ir.model'].search([('model', '=', 'hr.change.ticket')], limit=1).id,
            'icon': 'fa-pencil-square-o',
            'date_deadline': fields.Date.today(),
            'user_id': self.project_manager.id,
            'note': 'The request for change ticket is approved'
        }
        self.env['mail.activity'].create(notification)

        template_id = self.env.ref('hr_custom.email_after_change_ticket_approved')
        composer = self.env['mail.compose.message'].sudo().with_context({
            'default_composition_mode': 'mass_mail',
            'default_notify': False,
            'default_model': 'hr.change.ticket',
            'default_res_id': self.id,
            'default_template_id': template_id.id,
        }).create({})
        values = composer.onchange_template_id(template_id.id, 'mass_mail', 'hr.change.ticket', self.id)['value']
        composer.write(values)
        composer.send_mail()

        self.state = 'issued'

    @api.multi
    def action_cancel(self):
        self.state = 'cancelled'

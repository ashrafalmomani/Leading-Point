# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions
from datetime import timedelta
from odoo.exceptions import ValidationError


class HREmployeeTickets(models.Model):
    _name = "hr.tickets"
    _description = 'Tickets'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'employee_id'

    @api.model
    def _default_officer_user_id(self):
        return self.env['res.users'].search([('groups_id', 'in', self.env.ref('hr_custom.group_ticket_officer').id)],
                                            limit=1,
                                            order="id desc")

    @api.multi
    def _compute_per_diem(self):
        for per_diem in self:
            per_diem.per_diem_count = len(per_diem.per_diem_ids)

    employee_id = fields.Many2one('hr.employee', string='Employee')
    ticket_num = fields.Char(string='Ticket Number', track_visibility='always')
    country_id = fields.Many2one('res.country', string='Country', track_visibility='always')
    departure_date = fields.Datetime(string='Departure Date', track_visibility='always')
    return_date = fields.Datetime(string='Return Date', track_visibility='always')
    new_departure_date = fields.Datetime(string='New Departure Date', track_visibility='always')
    new_return_date = fields.Datetime(string='New Return Date', track_visibility='always')
    cost = fields.Float(string='Cost', track_visibility='always')
    ticket = fields.Binary(string='UPLOAD YOUR FILE', track_visibility='always')
    notes = fields.Char(string='Notes', track_visibility='always')
    officer_user_id = fields.Many2one('res.users', default=_default_officer_user_id)
    project_manager = fields.Many2one('hr.employee', string='Project Manager', track_visibility='always')
    reject_des = fields.Text(string='Reject Reason')
    analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    other_info = fields.Text(string='Other Description', track_visibility='always')
    per_diem_count = fields.Integer(compute='_compute_per_diem', string='Per Diem Lines')
    per_diem_ids = fields.One2many('per.diem.line', 'ticket_id', string='Per Diem')
    reservation_ids = fields.One2many('change.reservation.list', 'reservation_id', string='Projects/Leads', track_visibility='always')
    percentage_ids = fields.One2many('projects.travels', 'ticket_id', string='Projects/Leads', track_visibility='always')
    is_confirm_true = fields.Boolean(string='True', default=False)
    reason_for_travel = fields.Selection([('project', 'Project'), ('business_dev', 'Business Development'),
                                          ('visa_renewal', 'Visa Renewal'), ('other', 'Other')],
                                         string='Reason For Travel', track_visibility='always')
    type = fields.Selection([('new_ticket', 'New Ticket'), ('change_reservation', 'Change Reservation')], string='Type', track_visibility='always')
    airline = fields.Selection([('emirates', 'Emirates Airlines'), ('saudi', 'Saudi Airlines'),
                                ('royal', 'Royal Jordanian'), ('qatar', 'Qatar Airways'), ('oman', 'Oman Air'),
                                ('gulf', 'Gulf Air')], string='Airline', track_visibility='always')
    state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted'), ('issued', 'Issued'), ('closed', 'Closed'), ('rejected', 'Rejected')],
                             default='draft', store=True, track_visibility='always')

    @api.constrains('percentage_ids')
    def check_percentages(self):
        if self.reason_for_travel in ('project', 'business_dev'):
            totals = 0
            for rec in self.percentage_ids:
                totals += rec.percentage
            if totals != 100:
                raise exceptions.ValidationError(_("Total distribution of percentages must be 100%!"))

    @api.onchange('percentage_ids')
    def _onchange_project_lead(self):
        for rec in self.percentage_ids:
            if self.reason_for_travel == 'project':
                if rec.project_id:
                    employee = self.env['hr.employee'].search([('user_id', '=', rec.project_id.user_id.id)])
                    if employee:
                        self.project_manager = employee.id
            elif self.reason_for_travel == 'business_dev':
                employee = self.env['hr.employee'].search([('user_id', '=', rec.lead_id.user_id.id)])
                self.project_manager = employee.id

    @api.onchange('departure_date', 'return_date')
    def _onchange_new_departure_and_return(self):
        if self.departure_date:
            self.new_departure_date = self.departure_date
        if self.return_date:
            self.new_return_date = self.return_date

    @api.model
    def create(self, vals):
        if vals['reason_for_travel'] in ('project', 'business_dev') and 'percentage_ids' not in vals:
            raise exceptions.ValidationError(_("Please select projects or leads!"))
        return super(HREmployeeTickets, self).create(vals)


    @api.multi
    def action_submit(self):
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
    def action_issued(self):
        if self.reason_for_travel in ('project', 'business_dev'):
            for rec in self.percentage_ids:
                self.env['account.analytic.line'].create({
                    'name': "Ticket for (%s) " % self.employee_id.name,
                    'project_id': rec.project_id.id or False,
                    'account_id': rec.project_id.analytic_account_id.id or rec.lead_id.analytic_id.id,
                    'amount': self.cost * (rec.percentage / 100),
                    'unit_amount': 1,
                    'user_id': self.employee_id.user_id.id,
                    'date': fields.Date.today(),
                    'partner_id': self.employee_id.user_id.partner_id.id,
                })

            notification = {
                'activity_type_id': self.env.ref('hr_custom.notification_after_ticket_issued').id,
                'res_id': self.id,
                'res_model_id': self.env['ir.model'].search([('model', '=', 'hr.tickets')], limit=1).id,
                'icon': 'fa-pencil-square-o',
                'date_deadline': fields.Date.today(),
                'user_id': self.project_manager.id,
                'note': 'The requested ticket for (' + self.employee_id.name + ') employee hsa been issued'
            }
            self.env['mail.activity'].create(notification)

            template_id = self.env.ref('hr_custom.email_after_ticket_issued')
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

        else:
            self.env['account.analytic.line'].create({
                'name': "Ticket for (%s) " % self.employee_id.name,
                'account_id': self.analytic_id.id,
                'amount': self.cost,
                'unit_amount': 1,
                'user_id': self.employee_id.user_id.id,
                'date': fields.Date.today(),
                'partner_id': self.employee_id.user_id.partner_id.id,
            })

        self.state = 'issued'

    @api.multi
    def action_ticket_rejected(self):
        if not self.reject_des:
            raise ValidationError('You must insert the reject reason!')
        else:
            self.state = 'rejected'

        if self.reason_for_travel in ('project', 'business_dev'):
            reject_notification = {
                'activity_type_id': self.env.ref('hr_custom.notification_when_reject_ticket').id,
                'res_id': self.id,
                'res_model_id': self.env['ir.model'].search([('model', '=', 'hr.tickets')], limit=1).id,
                'icon': 'fa-pencil-square-o',
                'date_deadline': fields.Date.today(),
                'user_id': self.project_manager.id,
                'note': self.reject_des
            }
            self.env['mail.activity'].create(reject_notification)

    @api.multi
    def action_change_reservation(self, data):
        data['form'] = {}
        return {
            'name': _('New Reservation'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'change.reservation',
            'view_id': self.env.ref('hr_custom.change_reservation_view_wizard').id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

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
                    'note': 'Tomorrow the employee ('+ ticket.employee_id.name +') will travel please, pay attention if there is a change in ticket information'
                }
                self.env['mail.activity'].create(notification)

    @api.multi
    def per_diem_lines_view(self):
        return {
            'name': _('Per Diem Lines'),
            'domain': [('ticket_id', '=', self.id)],
            'res_model': 'per.diem.line',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'target': 'current'}

    @api.multi
    def change_status_to_closed(self):
        if self.new_return_date.date() == fields.date.today():
            self.state = 'closed'


class PerDiemLine(models.Model):
    _name = "per.diem.line"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Travel Per Diem Line'
    _rec_name = 'ticket_id'

    ticket_id = fields.Many2one('hr.tickets', string='Ticket')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    contract_id = fields.Many2one('hr.contract', 'Contract')
    amount = fields.Float('Amount')
    from_date = fields.Date('From Date')
    to_date = fields.Date('To Date')
    state = fields.Selection([('not_paid', 'Not Paid'), ('paid', 'Paid')], 'Status')

    @api.constrains('from_date', 'to_date')
    def _check_date(self):
        for perdiem in self:
            domain = [
                ('from_date', '=', perdiem.from_date),
                ('to_date', '>', perdiem.to_date),
                ('employee_id', '=', perdiem.employee_id.id),
                ('id', '!=', perdiem.id),
            ]
            perdiems = self.search_count(domain)
            if perdiems:
                raise ValidationError(_('The per diem calculated before.'))


class ChangeReservation(models.TransientModel):
    _name = "change.reservation"

    ticket_id = fields.Many2one('hr.tickets', string='Ticket')
    departure_date = fields.Datetime(string='Departure Date', track_visibility='always')
    return_date = fields.Datetime(string='Return Date', track_visibility='always')
    cost = fields.Float(string='Cost', track_visibility='always')

    @api.multi
    def confirm_change_reservation(self):
        active_id = self._context.get('active_id')
        ticket_id = self.env['hr.tickets'].browse(active_id)
        list_id = self.env['change.reservation.list'].create({'departure_date': self.departure_date,
                                                              'return_date': self.return_date,
                                                              'cost': self.cost})
        ticket_id.reservation_ids = list_id and [(4, list_id.id)] or False

        ticket = self.env['hr.tickets'].search([('state', '=', 'issued')], limit=1, order='id desc')
        if ticket.reason_for_travel in ('project', 'business_dev'):
            for rec in ticket.percentage_ids:
                self.env['account.analytic.line'].create({
                    'name': "Update Ticket for (%s) " % ticket.employee_id.name,
                    'project_id': rec.project_id.id or False,
                    'account_id': rec.project_id.analytic_account_id.id or rec.lead_id.analytic_id.id,
                    'amount': self.cost * (rec.percentage / 100),
                    'unit_amount': 1,
                    'user_id': ticket.employee_id.user_id.id,
                    'date': fields.Date.today(),
                    'partner_id': ticket.employee_id.user_id.partner_id.id,
                })
        else:
            self.env['account.analytic.line'].create({
                'name': "Update Ticket for (%s) " % ticket.employee_id.name,
                'account_id': ticket.analytic_id.id,
                'amount': self.cost,
                'unit_amount': 1,
                'user_id': ticket.employee_id.user_id.id,
                'date': fields.Date.today(),
                'partner_id': ticket.employee_id.user_id.partner_id.id,
            })

        if self.departure_date:
            ticket.new_departure_date = self.departure_date
        if self.return_date:
            ticket.new_return_date = self.return_date

        ticket.is_confirm_true = True


class ChangeReservationList(models.Model):
    _name = "change.reservation.list"

    reservation_id = fields.Many2one('hr.tickets', string='Reservation Update')
    departure_date = fields.Datetime(string='Departure Date', track_visibility='always')
    return_date = fields.Datetime(string='Return Date', track_visibility='always')
    cost = fields.Float(string='Cost', track_visibility='always')



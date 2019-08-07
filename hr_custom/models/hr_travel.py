# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions
from odoo.exceptions import ValidationError
from datetime import timedelta


class HREmployeeTravel(models.Model):
    _name = "hr.travel"
    _description = 'Travel'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    @api.depends('state', 'ticket_ids', 'visa_ids', 'hotel_ids')
    def _compute_trip_status(self):
        for rec in self:
            visa = False
            hotel = False
            ticket = False
            open_travel = False
            close_travel = False
            if rec.state in ('draft', 'submitted', 'manager_approved'):
                rec.trip_status = 'not_started'

            if rec.state == 'hr_approved':
                rec.trip_status = 'preparing'

                if rec.visa_required and rec.hotel_required:
                    visa_id = rec.visa_ids.ids[-1]
                    if self.env['hr.visas'].browse(visa_id).state == 'posted':
                        visa = True

                    if rec.hotel_ids:
                        hotel_id = rec.hotel_ids.ids[-1]
                        if self.env['hr.hotels'].browse(hotel_id).state == 'reserved':
                            hotel = True

                    if rec.ticket_ids:
                        ticket_id = rec.ticket_ids.ids[-1]
                        last_ticket = self.env['hr.tickets'].browse(ticket_id)
                        if last_ticket.departure_date.date() <= fields.Date.today() and last_ticket.state == 'issued':
                            open_travel = True
                        elif last_ticket.return_date.date() <= fields.Date.today() and last_ticket.state == 'issued':
                            close_travel = True
                        elif last_ticket.state == 'issued':
                            ticket = True

                    if open_travel:
                        rec.trip_status = 'open'
                    elif close_travel:
                        rec.trip_status = 'closed'
                    if visa and hotel and ticket:
                        rec.trip_status = 'ready'

                elif rec.visa_required and not rec.hotel_required:
                    visa_id = rec.visa_ids.ids[-1]
                    if self.env['hr.visas'].browse(visa_id).state == 'posted':
                        visa = True

                    if rec.ticket_ids:
                        ticket_id = rec.ticket_ids.ids[-1]
                        last_ticket = self.env['hr.tickets'].browse(ticket_id)
                        if last_ticket.departure_date.date() <= fields.Date.today() and last_ticket.state == 'issued':
                            open_travel = True
                        elif last_ticket.return_date.date() <= fields.Date.today() and last_ticket.state == 'issued':
                            close_travel = True
                        elif last_ticket.state == 'issued':
                            ticket = True

                    if open_travel:
                        rec.trip_status = 'open'
                    elif close_travel:
                        rec.trip_status = 'closed'
                    if visa and ticket:
                        rec.trip_status = 'ready'

                elif not rec.visa_required and rec.hotel_required:
                    if rec.hotel_ids:
                        hotel_id = rec.hotel_ids.ids[-1]
                        if self.env['hr.hotels'].browse(hotel_id).state == 'reserved':
                            hotel = True

                    if rec.ticket_ids:
                        ticket_id = rec.ticket_ids.ids[-1]
                        last_ticket = self.env['hr.tickets'].browse(ticket_id)
                        if last_ticket.departure_date.date() <= fields.Date.today() and last_ticket.state == 'issued':
                            open_travel = True
                        elif last_ticket.return_date.date() <= fields.Date.today() and last_ticket.state == 'issued':
                            close_travel = True
                        elif last_ticket.state == 'issued':
                            ticket = True

                    if open_travel:
                        rec.trip_status = 'open'
                    elif close_travel:
                        rec.trip_status = 'closed'
                    if hotel and ticket:
                        rec.trip_status = 'ready'

                elif not rec.visa_required and not rec.hotel_required:
                    if rec.ticket_ids:
                        ticket_id = rec.ticket_ids.ids[-1]
                        last_ticket = self.env['hr.tickets'].browse(ticket_id)
                        if last_ticket.departure_date.date() <= fields.Date.today() and last_ticket.state == 'issued':
                            rec.trip_status = 'open'
                        elif last_ticket.return_date.date() <= fields.Date.today() and last_ticket.state == 'issued':
                            rec.trip_status = 'closed'
                        elif last_ticket.state == 'issued':
                            rec.trip_status = 'ready'

    def _default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    name = fields.Char(string='Name', required=True, copy=False, default='New', track_visibility='always')
    number = fields.Char('Number', required=True, copy=False, default='New', track_visibility='always')
    employee = fields.Many2one('hr.employee', string='Employee', default=_default_employee, track_visibility='always')
    analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    origin = fields.Many2one('res.country.state', string='Origin', track_visibility='always')
    destination = fields.Many2one('res.country.state', string='Destination', track_visibility='always')
    from_date = fields.Date(string='From Date', track_visibility='always')
    to_date = fields.Date(string='To Date', track_visibility='always')
    visa_required = fields.Boolean(string='Is Visa Required', track_visibility='always')
    hotel_required = fields.Boolean(string='Is Hotel Required', track_visibility='always')
    other_info = fields.Text(string='Other Description', track_visibility='always')
    reject_des = fields.Text(string='Reject Reason')
    ticket_ids = fields.One2many('hr.tickets', 'travel_id', string='Tickets', track_visibility='always')
    hotel_ids = fields.One2many('hr.hotels', 'travel_id', string='Hotels', track_visibility='always')
    visa_ids = fields.One2many('hr.visas', 'travel_id', string='Visas', track_visibility='always')
    percentage_ids = fields.One2many('projects.travels', 'travel_id', string='Projects/Leads', track_visibility='always')
    project_manager = fields.Many2one('hr.employee', string='Project Manager', track_visibility='always')
    direct_manager = fields.Many2one('hr.employee', string='Direct Manager', track_visibility='always')
    reason_for_travel = fields.Selection([('project', 'Project'), ('business_dev', 'Business Development'),
                                          ('visa_renewal', 'Visa Renewal'), ('other', 'Other')],
                                         string='Reason For Travel', track_visibility='always')
    state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted'), ('manager_approved', 'Manager Approved'),
                              ('hr_approved', 'HR Approval'), ('rejected', 'Rejected')],
                             default='draft', store=True, track_visibility='always')
    trip_status = fields.Selection([('not_started', 'Not Started'), ('preparing', 'Preparing'), ('ready', 'Ready'),
                                    ('open', 'Open'), ('closed', 'Closed'), ('cancel', 'Cancel')],
                                   compute=_compute_trip_status, string='Trip Status', store=True,
                                   default='not_started', track_visibility='always')

    @api.one
    @api.constrains('origin', 'destination')
    def check_origin_and_destination(self):
        if self.origin == self.destination:
            raise exceptions.ValidationError(_("Origin and Destination are same!"))

    @api.constrains('from_date', 'to_date')
    def _check_date(self):
        for travel in self:
            domain = [
                ('from_date', '<', travel.to_date),
                ('to_date', '>', travel.from_date),
                ('employee', '=', travel.employee.id),
                ('id', '!=', travel.id),
                ('state', '!=', 'rejected'),
            ]
            travels = self.search_count(domain)
            if travels:
                raise ValidationError(_('You can not have 2 travel that overlaps on the same day.'))

    @api.constrains('percentage_ids',)
    def check_origin_and_destination(self):
        if self.reason_for_travel in ('project', 'business_dev'):
            totals = 0
            for rec in self.percentage_ids:
                totals += rec.percentage
            if totals != 100:
                raise exceptions.ValidationError(_("Total distribution of percentages must be 100%!"))

    @api.onchange('employee')
    def _onchange_employee(self):
        if self.employee:
            self.direct_manager = self.employee.parent_id.id

    @api.onchange('percentage_ids')
    def _onchange_project_lead(self):
        for rec in self.percentage_ids:
            if self.reason_for_travel == 'project':
                employee = self.env['hr.employee'].search([('user_id', '=', rec.project_id.user_id.id)])
                if employee:
                    self.project_manager = employee.id
            elif self.reason_for_travel == 'business_dev':
                self.project_manager = rec.lead_id.owner.id

    @api.model
    def create(self, vals):
        if vals['reason_for_travel'] in ('project', 'business_dev') and 'percentage_ids' not in vals:
            raise exceptions.ValidationError(_("Please select projects or leads!"))
        number = self.env['ir.sequence'].next_by_code('hr.travel') or '/'
        employee = self.env['hr.employee'].browse(vals['employee']).name
        vals.update({'number': number, 'name': employee + number})
        return super(HREmployeeTravel, self).create(vals)

    @api.multi
    def action_submit(self):
        self.state = 'submitted'

    @api.multi
    def action_approve_by_manager(self):
        self.state = 'manager_approved'

    @api.multi
    def action_hr_approve(self):
        if self.visa_required:
            self.env['hr.visas'].create({'travel_id': self.id, 'state': 'pending'})
        self.state = 'hr_approved'

    @api.multi
    def action_reject(self):
        if not self.reject_des:
            raise ValidationError('You must insert the reject reason!')
        else:
            self.state = 'rejected'

        user_id = self.env['res.users'].search([('groups_id', 'in', self.env.ref('hr.group_hr_manager').id)], limit=1, order="id desc")
        reject_notification = {
            'activity_type_id': self.env.ref('hr_custom.mail_activity_travel_reject_notification').id,
            'res_id': self.id,
            'res_model_id': self.env['ir.model'].search([('model', '=', 'hr.travel')], limit=1).id,
            'icon': 'fa-pencil-square-o',
            'date_deadline': fields.Datetime.now(),
            'user_id': user_id.id,
            'note': self.reject_des
        }
        self.env['mail.activity'].create(reject_notification)

    @api.multi
    def action_set_to_draft(self):
        self.state = 'draft'

    @api.multi
    def action_cancel_travel(self):
        if self.visa_ids:
            for visa in self.visa_ids:
                visa.write({'state': 'cancel'})
        if self.ticket_ids:
            for ticket in self.ticket_ids:
                ticket.write({'state': 'cancelled'})
        if self.hotel_ids:
            for hotel in self.hotel_ids:
                hotel.write({'state': 'cancel'})
        self.state = 'cancel'

    @api.multi
    def send_email_before_change_status(self):
        travels = self.env['hr.travel'].search([('trip_status', 'in', ('ready', 'open'))])
        for travel in travels:
            if travel.state == 'ready':
                date = travel.from_date - timedelta(days=2)
                template_id = self.env.ref('hr_custom.email_template_open_travel').id
            else:
                date = travel.to_date - timedelta(days=2)
                template_id = self.env.ref('jao_sales.email_template_close_travel').id

            if date == fields.Date.today():
                composer = self.env['mail.compose.message'].sudo().with_context({
                    'default_composition_mode': 'mass_mail',
                    'default_notify': False,
                    'default_model': 'hr.travel',
                    'default_res_id': travel.id,
                    'default_template_id': template_id,
                }).create({})
                values = composer.onchange_template_id(template_id, 'mass_mail', 'hr.travel', travel.id)['value']
                composer.write(values)
                composer.send_mail()


class ProjectsTravels(models.Model):
    _name = "projects.travels"
    _description = 'Projects Travel'
    _rec_name = 'travel_id'

    travel_id = fields.Many2one('hr.travel', string='Travel')
    project_id = fields.Many2one('project.project', string='Project')
    lead_id = fields.Many2one('crm.lead', string='Lead/Opportunity')
    percentage = fields.Integer('Percentage(%)')


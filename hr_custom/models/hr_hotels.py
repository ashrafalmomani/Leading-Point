# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions
from odoo.exceptions import ValidationError


class HREmployeeHotels(models.Model):
    _name = "hr.hotels"
    _description = 'Hotels'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'employee_id'

    @api.model
    def _default_officer_user_id(self):
        return self.env['res.users'].search([('groups_id', 'in', self.env.ref('hr_custom.group_hotel_officer').id)],
                                            limit=1,
                                            order="id desc")

    employee_id = fields.Many2one('hr.employee', string='Employee')
    hotel_name = fields.Char(string='Hotel Name', track_visibility='always')
    reservation_num = fields.Char(string='Reservation Number', track_visibility='always')
    country_id = fields.Many2one('res.country', string='Country', track_visibility='always')
    check_in = fields.Date(string='Check In', track_visibility='always')
    check_out = fields.Date(string='Check Out', track_visibility='always')
    cost = fields.Float(string='Cost', track_visibility='always')
    reservation = fields.Binary(string='UPLOAD YOUR FILE', track_visibility='always')
    reject_des = fields.Text(string='Reject Reason')
    analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    other_info = fields.Text(string='Other Description', track_visibility='always')
    percentage_ids = fields.One2many('projects.travels', 'hotel_id', string='Projects/Leads', track_visibility='always')
    reason_for_travel = fields.Selection([('project', 'Project'), ('business_dev', 'Business Development'),
                                          ('visa_renewal', 'Visa Renewal'), ('other', 'Other')],
                                         string='Reason For Travel', track_visibility='always')
    state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted'), ('reserved', 'Reserved'), ('rejected', 'Rejected')],
                             default='draft', store=True, track_visibility='always')
    officer_user_id = fields.Many2one('res.users', default=_default_officer_user_id)
    project_manager = fields.Many2one('hr.employee', string='Project Manager', track_visibility='always')

    @api.constrains('percentage_ids', )
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

    @api.model
    def create(self, vals):
        if vals['reason_for_travel'] in ('project', 'business_dev') and 'percentage_ids' not in vals:
            raise exceptions.ValidationError(_("Please select projects or leads!"))
        return super(HREmployeeHotels, self).create(vals)

    @api.multi
    def action_submitted(self):
        notification = {
            'activity_type_id': self.env.ref('hr_custom.notification_after_hotel_submitted').id,
            'res_id': self.id,
            'res_model_id': self.env['ir.model'].search([('model', '=', 'hr.hotels')], limit=1).id,
            'icon': 'fa-pencil-square-o',
            'date_deadline': fields.Date.today(),
            'user_id': self.officer_user_id.id,
            'note': 'Request For Hotel'
        }
        self.env['mail.activity'].create(notification)

        template_id = self.env.ref('hr_custom.email_after_hotel_submitted')
        composer = self.env['mail.compose.message'].sudo().with_context({
            'default_composition_mode': 'mass_mail',
            'default_notify': False,
            'default_model': 'hr.hotels',
            'default_res_id': self.id,
            'default_template_id': template_id.id,
        }).create({})
        values = composer.onchange_template_id(template_id.id, 'mass_mail', 'hr.hotels', self.id)['value']
        composer.write(values)
        composer.send_mail()

        self.state = 'submitted'

    @api.multi
    def action_reserved(self):
        if self.reason_for_travel in ('project', 'business_dev'):
            for rec in self.percentage_ids:
                self.env['account.analytic.line'].create({
                    'name': "Hotel for (%s) " % self.employee_id.name,
                    'project_id': rec.project_id.id or False,
                    'account_id': rec.project_id.analytic_account_id.id or rec.lead_id.analytic_id.id,
                    'amount': self.cost * (rec.percentage / 100),
                    'unit_amount': 1,
                    'user_id': self.employee_id.user_id.id,
                    'date': fields.Date.today(),
                    'partner_id': self.employee_id.user_id.partner_id.id,
                })

            notification = {
                'activity_type_id': self.env.ref('hr_custom.notification_after_hotel_reserved').id,
                'res_id': self.id,
                'res_model_id': self.env['ir.model'].search([('model', '=', 'hr.hotels')], limit=1).id,
                'icon': 'fa-pencil-square-o',
                'date_deadline': fields.Date.today(),
                'user_id': self.project_id.user_id.id,
                'note': 'The requested hotel for (' + self.employee_id.name + ') employee hsa been reserved'
            }
            self.env['mail.activity'].create(notification)

            template_id = self.env.ref('hr_custom.email_after_hotel_reserved')
            composer = self.env['mail.compose.message'].sudo().with_context({
                'default_composition_mode': 'mass_mail',
                'default_notify': False,
                'default_model': 'hr.hotels',
                'default_res_id': self.id,
                'default_template_id': template_id.id,
            }).create({})
            values = composer.onchange_template_id(template_id.id, 'mass_mail', 'hr.hotels', self.id)['value']
            composer.write(values)
            composer.send_mail()

        else:
            self.env['account.analytic.line'].create({
                'name': "Hotel for (%s) " % self.employee_id.name,
                'account_id': self.analytic_id.id,
                'amount': self.cost,
                'unit_amount': 1,
                'user_id': self.employee_id.user_id.id,
                'date': fields.Date.today(),
                'partner_id': self.employee_id.user_id.partner_id.id,
            })

        self.state = 'reserved'

    @api.multi
    def action_hotel_rejected(self):
        if not self.reject_des:
            raise ValidationError('You must insert the reject reason!')
        else:
            self.state = 'rejected'
        if self.reason_for_travel in ('project', 'business_dev'):
            reject_notification = {
                'activity_type_id': self.env.ref('hr_custom.notification_when_reject_hotel').id,
                'res_id': self.id,
                'res_model_id': self.env['ir.model'].search([('model', '=', 'hr.hotels')], limit=1).id,
                'icon': 'fa-pencil-square-o',
                'date_deadline': fields.Date.today(),
                'user_id': self.project_manager.id,
                'note': self.reject_des
            }
            self.env['mail.activity'].create(reject_notification)

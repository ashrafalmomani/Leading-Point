# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions
from odoo.exceptions import ValidationError


class HrAwardedDays(models.Model):
    _name = 'hr.awarded.days'
    _description = 'Awarded Days'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    @api.one
    @api.depends('awarded_ids', 'total_hour')
    def _compute_total_hours(self):
        total = 0
        for rec in self.awarded_ids:
            total += rec.hours
        if total >= 0:
            self.total_hour = total

    name = fields.Char(string='Name', required=True, copy=False, default='New', track_visibility='always')
    number_seq = fields.Char(string='Number', required=True, copy=False, default='New', track_visibility='always')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    user_id = fields.Many2one('res.users', string='User', related='employee_id.user_id')
    awarded_ids = fields.One2many('hr.award.line', 'awarded_id', string='Details', track_visibility='always')
    projects = fields.Many2many('project.project', string='Project', track_visibility='always')
    lead = fields.Many2many('crm.lead', string='Lead/Opportunity', track_visibility='always')
    other_des = fields.Text(string='Other Description')
    reject_des = fields.Text(string='Reject Reason')
    is_paid = fields.Boolean(string='Is Paid?')
    project_manager = fields.Many2one('hr.employee', string='Project/lead Manager', track_visibility='always')
    direct_manager = fields.Many2one('hr.employee', string='Direct Manager', track_visibility='always')
    total_hour = fields.Float(string='Total Hours', compute=_compute_total_hours, track_visibility='always', store=True)
    related_to = fields.Selection([('project', 'Project'),
                                   ('business_dev', 'Business Development'),
                                   ('admin', 'Administration'),
                                   ('other', 'Other')], string='Related To', track_visibility='always')
    state = fields.Selection([('draft', 'Draft'),
                              ('submitted', 'Submitted'),
                              ('manager_approved', 'Manager Approved'),
                              ('hr_approved', 'HR Approval'),
                              ('rejected', 'Rejected')], string="Status", default='draft', store=True, track_visibility='always')

    @api.multi
    @api.constrains('awarded_ids')
    def check_details_tree_hours(self):
        for rec in self.awarded_ids:
            if rec.hours == 0:
                raise exceptions.ValidationError(_("Some items in the award details are not valid !"))

    @api.onchange('employee_id')
    def _onchange_employee_and_manager(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
        if employee:
            self.employee_id = employee.id
            self.direct_manager = employee.parent_id.id

    @api.onchange('related_to')
    def _onchange_related_to(self):
        if self.related_to == 'project':
            self.lead = False
        elif self.related_to == 'business_dev':
            self.projects = False
        else:
            self.projects = False
            self.lead = False

    @api.onchange('projects')
    def _onchange_project(self):
        for rec in self.projects:
            employee = self.env['hr.employee'].search([('user_id', '=', rec.user_id.id)])
            if employee:
                self.project_manager = employee.id

    @api.onchange('lead')
    def _onchange_lead(self):
        for rec in self.lead:
            self.project_manager = rec.owner.id

    @api.model
    def create(self, vals):
        if 'awarded_ids' not in vals:
            raise exceptions.ValidationError(_("Please enter valid awarded days greated than zero !"))
        number_seq = self.env['ir.sequence'].next_by_code('hr.awarded.days') or '/'
        employee = self.env['hr.employee'].browse(vals['employee_id']).name
        vals.update({'number_seq': number_seq, 'name': employee + number_seq})
        return super(HrAwardedDays, self).create(vals)

    @api.multi
    def action_submit(self):
        self.state = 'submitted'
        self.message_needaction = True

        activity_record = {
            'activity_type_id': self.env.ref('hr_custom.mail_activity_data_award_approval').id,
            'res_id': self.id,
            'res_model_id': self.env['ir.model'].search([('model', '=', 'hr.awarded.days')], limit=1).id,
            'icon': 'fa-pencil-square-o',
            'date_deadline': fields.Datetime.now(),
            'user_id': self.project_manager.user_id.id or 1,
            'note': 'Awarded Days Approval'
        }
        self.env['mail.activity'].create(activity_record)

    @api.multi
    def action_manager_approved(self):
        self.state = 'manager_approved'

    @api.multi
    def action_hr_approved(self):
        self.state = 'hr_approved'

    @api.multi
    def action_reject(self):
        if not self.reject_des:
            raise ValidationError('You must insert the reject reason!')
        else:
            self.state = 'rejected'

        reject_notification = {
            'activity_type_id': self.env.ref('hr_custom.mail_activity_reject_notification').id,
            'res_id': self.id,
            'res_model_id': self.env['ir.model'].search([('model', '=', 'hr.awarded.days')], limit=1).id,
            'icon': 'fa-pencil-square-o',
            'date_deadline': fields.Datetime.now(),
            'user_id': self.employee_id.user_id.id,
            'note': self.reject_des
        }
        self.env['mail.activity'].create(reject_notification)

    @api.multi
    def action_send_to_draft(self):
        self.state = 'draft'


class HrAwardLine(models.Model):
    _name = 'hr.award.line'
    _description = 'Award Line'

    awarded_id = fields.Many2one('hr.awarded.days', string='Details', track_visibility='always')
    description = fields.Char(string='Description', track_visibility='always')
    date = fields.Date(string='Date', track_visibility='always')
    hours = fields.Float(string='Hours', track_visibility='always')
    reason = fields.Selection([('travel', 'Travel'),
                               ('overtime', 'Overtime Work')], string='Reason', track_visibility='always')

    @api.multi
    @api.constrains('reason', 'hours')
    def check_reason_hours(self):
        for rec in self:
            if rec.reason == 'travel':
                if rec.hours > 8:
                    raise exceptions.ValidationError(_("The maximum hours for travel reason is 8 hours !"))

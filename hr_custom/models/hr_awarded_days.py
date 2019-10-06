# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError


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

    def _default_employee_id(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])

    def _default_direct_manager_id(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1).parent_id

    name = fields.Char(string='Name', required=True, copy=False, default='New', track_visibility='always')
    number_seq = fields.Char(string='Number', required=True, copy=False, default='New', track_visibility='always')
    employee_id = fields.Many2one('hr.employee', string='Employee', default=_default_employee_id)
    user_id = fields.Many2one('res.users', string='User', related='employee_id.user_id')
    awarded_ids = fields.One2many('hr.award.line', 'awarded_id', string='Details', track_visibility='always')
    projects = fields.Many2many('project.project', string='Project', track_visibility='always')
    lead = fields.Many2many('crm.lead', string='Lead/Opportunity', track_visibility='always')
    other_des = fields.Text(string='Other Description')
    reject_des = fields.Text(string='Reject Reason')
    is_paid = fields.Boolean(string='Is Paid?')
    include_salary = fields.Boolean(string='Include Salary', default=True)
    project_manager = fields.Many2one('hr.employee', string='Project/lead Manager', track_visibility='always')
    direct_manager = fields.Many2one('hr.employee', string='Direct Manager', track_visibility='always', default=_default_direct_manager_id)
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
        if self.employee_id:
            self.direct_manager = self.employee_id.parent_id.id

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
            employee = self.env['hr.employee'].search([('user_id', '=', rec.user_id.id)])
            if employee:
                self.project_manager = employee.id

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
    def action_reject(self, data):
        data['form'] = {}
        return {
            'name': _('Reject Reason'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'reject.reason',
            'view_id': self.env.ref('hr_custom.view_reject_reason_wizard').id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }


    @api.multi
    def action_send_to_draft(self):
        self.state = 'draft'

    @api.multi
    def action_generate_entries(self):
        config_id = self.env['res.config.settings'].search([('awarded_account_id', '!=', False), ('awarded_days_journal_id', '!=', False)])
        if not config_id.awarded_account_id or not config_id.awarded_days_journal_id:
            raise UserError(_('Please set up awarded days account and journal from settings menu.'))
        credit_emp_acc = self.employee_id.user_id.partner_id.property_account_payable_id.id
        move_line_values = []
        move_obj = self.env['account.move']
        journal_id = config_id.awarded_days_journal_id.id
        contract_id = self.employee_id.contract_id
        amount = ((contract_id.wage + contract_id.salary_raise) / 30 / 8) * self.total_hour
        debit_value = {
            'name': 'Awarded Days for ' + self.employee_id.name + ' #' + self.number_seq,
            'account_id': config_id.awarded_account_id.id,
            'debit': amount,
            'credit': 0.0,
            'journal_id': journal_id,
            'partner_id': self.employee_id.user_id.partner_id.id}
        move_line_values.append([0, False, debit_value])
        credit_value = {
            'name': 'Awarded Days for ' + self.employee_id.name + ' #' + self.number_seq,
            'account_id': credit_emp_acc,
            'debit': 0.0,
            'credit': amount,
            'journal_id': journal_id,
            'partner_id': self.employee_id.user_id.partner_id.id}
        move_line_values.append([0, False, credit_value])
        if move_line_values:
            move_id = move_obj.create({
                'date': fields.Date.today(),
                'ref': 'Awarded Days #' + self.number_seq,
                'journal_id': journal_id,
                'company_id': self.env.user.company_id.id,
                'partner_id': self.employee_id.user_id.partner_id.id,
                'line_ids': move_line_values
            })
            move_id.post()
        self.is_paid = True


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

    @api.onchange('reason')
    def _set_default_hour(self):
        for rec in self:
            if rec.reason == 'travel':
                rec.hours = 8.0


class RejectReason(models.TransientModel):
    _name = "reject.reason"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    reject_reason = fields.Text(string='Reason')

    @api.multi
    def confirm_reject_reason(self):
        active_id = self._context.get('active_id')
        awarded_days_id = self.env['hr.awarded.days'].browse(active_id)
        awarded_days_id.write({'reject_des': self.reject_reason, 'state': 'rejected'})

        for rec in self.env['hr.awarded.days'].search([('state', '=', 'rejected')], limit=1, order="id desc"):
            reject_notification = {
                'activity_type_id': self.env.ref('hr_custom.mail_activity_reject_notification').id,
                'res_id': rec.id,
                'res_model_id': self.env['ir.model'].search([('model', '=', 'hr.awarded.days')], limit=1).id,
                'icon': 'fa-pencil-square-o',
                'date_deadline': fields.Datetime.now(),
                'user_id': rec.employee_id.user_id.id,
                'note': rec.reject_des
            }
            self.env['mail.activity'].create(reject_notification)


# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime
from dateutil import relativedelta
from datetime import timedelta


class HumanResourceCustom(models.Model):
    _inherit = "hr.employee"

    @api.model
    def _get_default_category(self):
        return self.env.ref('hr_custom.employee_less_than_tags')

    @api.model
    def _get_default_hr_manager(self):
        return self.env['res.users'].search([('groups_id', 'in', self.env.ref('hr.group_hr_manager').id)],
                                            limit=1,
                                            order="id desc")

    joining_date = fields.Date(string='Joining Date')
    arabic_name = fields.Char(string='Name in Arabic')
    current_contract_start = fields.Date(string='Current Contract Start', compute='compute_current_contract_start')
    document_ids = fields.One2many('document.line', 'employee_id', string='Document')
    user_check_tick = fields.Boolean(default=False)
    hr_manager_id = fields.Many2one('res.users', string='HR Manager', default=_get_default_hr_manager)
    category_ids = fields.Many2many('hr.employee.category', 'employee_category_rel', 'emp_id', 'category_id', string='Tags', default=_get_default_category)

    @api.model
    def create(self, vals):
        res = super(HumanResourceCustom, self).create(vals)
        annual_leave_month = 14 / 12
        annual_leave_day = annual_leave_month / 30
        current_date = datetime.datetime.strptime(vals['joining_date'], '%Y-%m-%d').date()
        end_of_year = datetime.date(year=current_date.year, month=12, day=31)
        diff_month = relativedelta.relativedelta(end_of_year, current_date).months
        diff_day = relativedelta.relativedelta(end_of_year, current_date).days
        diff_days = diff_day * annual_leave_day
        diff_months = diff_month * annual_leave_month
        annual_leave = diff_months + diff_days

        allocation = self.env['hr.leave.allocation'].create({
            'name': "Legal Annual Leave",
            'holiday_status_id': 1,
            'number_of_days': annual_leave,
            'holiday_type': 'employee',
            'employee_id': res.id,
        })
        allocation.action_approve()

        allocation_sick = self.env['hr.leave.allocation'].create({
            'name': "Sick Leave",
            'holiday_status_id': 5,
            'number_of_days': annual_leave,
            'holiday_type': 'employee',
            'employee_id': res.id,
        })
        allocation_sick.action_approve()
        return res

    # @api.multi
    # def allocation_every_beginning_year(self):
    #     employees = self.env['hr.employee']
    #     for rec in employees:
    #         current_date = fields.Date.today()
    #         beginning_year = datetime.date(year=current_date.year, month=1, day=1)
    #         end_of_year = datetime.date(year=current_date.year, month=12, day=31)
    #         diff_months = relativedelta.relativedelta(end_of_year, beginning_year).months
    #         annual_leave = (14 / 12) * diff_months
    #
    #         allocation = self.env['hr.leave.allocation'].create({
    #             'name': "Legal Annual Leave",
    #             'holiday_status_id': 1,
    #             'number_of_days': annual_leave,
    #             'holiday_type': 'employee',
    #             'employee_id': employees,
    #         })
    #         allocation.action_approve()

    @api.multi
    def create_user(self):
        user_id = self.env['res.users'].create({'name': self.name, 'login': self.work_email})
        self.address_home_id = user_id.partner_id.id
        self.user_id = user_id.id
        self.user_check_tick = True
        self.work_email = user_id.email

    @api.onchange('address_home_id')
    def user_checking(self):
        if self.address_home_id:
            self.user_check_tick = True
        else:
            self.user_check_tick = False

    @api.onchange('department_id')
    def _onchange_manager(self):
        if self.department_id:
            self.manager_id = self.department_id.manager_id.id


    @api.multi
    def _check_employee_years(self):
        employees = self.env['hr.employee'].search([])
        for rec in employees:
            current_year = fields.Date.today()
            join = rec.joining_date
            if join:
                joining_year = fields.relativedelta(current_year, join).years
                less = self.env.ref('hr_custom.employee_less_than_tags').id
                more = self.env.ref('hr_custom.employee_more_than_tags').id
                if joining_year < 5:
                    rec.category_ids = [(6, 0, [less])]
                else:
                    rec.category_ids = [(6, 0, [more])]

    def compute_current_contract_start(self):
        for rec in self:
            if rec.contract_id:
                rec.current_contract_start = rec.contract_id.date_start

    @api.multi
    def email_before_one_week_from_joining_date(self):
        employees = self.env['hr.employee'].search([])
        for rec in employees:
            if rec.joining_date:
                after_three_month = rec.joining_date + relativedelta.relativedelta(months=+3)
                before_one_week = after_three_month - timedelta(days=7)
                if fields.Date.today() == before_one_week:
                    template_id = self.env.ref('hr_custom.email_before_one_week_from_joining_date')
                    composer = self.env['mail.compose.message'].sudo().with_context({
                        'default_composition_mode': 'mass_mail',
                        'default_notify': False,
                        'default_model': 'hr.employee',
                        'default_res_id': self.id,
                        'default_template_id': template_id.id,
                    }).create({})
                    values = composer.onchange_template_id(template_id.id, 'mass_mail', 'hr.employee', self.id)[
                        'value']
                    composer.write(values)
                    composer.send_mail()

    @api.multi
    def projects(self):
        return {
            'name': _('Projects'),
            'domain': [('members', 'in', [self.id])],
            'res_model': 'project.project',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'views': [(self.env.ref('project.view_project_kanban').id, 'kanban')],
            'view_type': 'kanban',
            'view_mode': 'kanban,',
            'target': 'current'}

    @api.multi
    def appraisal(self):
        return {
            'name': _('Appraisal'),
            'domain': [('employee_id', 'in', [self.id])],
            'context': {'default_employee_id': self.id},
            'res_model': 'hr.appraisal',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'views': [(self.env.ref('hr_custom.hr_appraisal_tree_view').id, 'tree'), (self.env.ref('hr_custom.hr_appraisal_form_view').id, 'form')],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'target': 'current'}

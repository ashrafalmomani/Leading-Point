# -*- coding: utf-8 -*-

from odoo import models, api, fields, _, exceptions
from odoo.exceptions import UserError


class PayrollCustom(models.Model):
    _inherit = 'hr.payslip.run'

    @api.multi
    def deduct_unpaid_vacations(self):
        for payslip in self.slip_ids:
            if not payslip.include_vacations:
                for leave in self.env['hr.leave'].search([('employee_id', '=', payslip.employee_id.id),
                                                          ('state', 'in', ('validate', 'validate1')),
                                                          ('is_deducted', '=', False),
                                                          ('include_in_salary', '=', True),
                                                          ('holiday_status_id.unpaid', '=', True)]):
                    holiday_name = 'Unpaid Leave (' + str(leave.request_date_from) + ' TO ' + str(leave.request_date_to) + ')'
                    amount = -(leave.salary / 30) * leave.number_of_days
                    payslip.input_line_ids.create({'payslip_id': payslip.id,
                                                   'name': holiday_name,
                                                   'code': 'Unpaid',
                                                   'amount': amount,
                                                   'contract_id': payslip.employee_id.contract_id.id,
                                                   'leave_id': leave.id})
                payslip.compute_sheet()
                payslip.include_vacations = True

    @api.multi
    def include_expenses(self):
        for payslip in self.slip_ids:
            if not payslip.include_expense:
                for awarded in self.env['hr.awarded.days'].search([('employee_id', '=', payslip.employee_id.id),
                                                                   ('state', '=', 'hr_approved'),
                                                                   ('is_paid', '=', False)]):
                    amount = 0.0
                    for rec in awarded.awarded_ids:
                        amount += (rec.salary / 30 / 8) * rec.hours

                    payslip.input_line_ids.create({'payslip_id': payslip.id,
                                                   'name': awarded.name,
                                                   'code': 'AwardedDays',
                                                   'amount': amount,
                                                   'contract_id': payslip.employee_id.contract_id.id,
                                                   'awarded_id': awarded.id})

                for expense in self.env['hr.expense.sheet'].search([('employee_id', '=', payslip.employee_id.id),
                                                                    ('state', '=', 'approve'),
                                                                    ('include_in_salary', '=', True)]):
                    payslip.input_line_ids.create({'payslip_id': payslip.id,
                                                   'name': expense.name,
                                                   'code': 'Expense',
                                                   'amount': expense.total_amount,
                                                   'contract_id': payslip.employee_id.contract_id.id,
                                                   'expense_id': expense.id})

                for per_diem in self.env['per.diem.line'].search([('employee_id', '=', payslip.employee_id.id),
                                                                  ('state', '=', 'not_paid'),
                                                                  ('from_date', '>=', payslip.date_from),
                                                                  ('to_date', '<=', payslip.date_to)]):
                    payslip.input_line_ids.create({'payslip_id': payslip.id,
                                                   'name': 'Per Diem for %s' % per_diem.employee_id.name,
                                                   'code': 'PerDiem',
                                                   'amount': per_diem.amount,
                                                   'contract_id': payslip.employee_id.contract_id.id,
                                                   'per_diem_id': per_diem.id})
                payslip.compute_sheet()
                payslip.include_expense = True


class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    leave_id = fields.Many2one('hr.leave', string='Leave')
    awarded_id = fields.Many2one('hr.awarded.days', string='Awarded Days')
    per_diem_id = fields.Many2one('per.diem.line', string='Per Diem')
    expense_id = fields.Many2one('hr.expense.sheet', string='Expense')


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    include_in_salary = fields.Boolean(string='Include In Salary', default=True)
    related_to = fields.Selection([('project', 'Project'),
                                   ('business_dev', 'Business Development'),
                                   ('other', 'Other')], string='Related To', track_visibility='always')
    percentage_ids = fields.One2many('projects.travels', 'expense_sheet_id', string='Projects/Leads',
                                     track_visibility='always')
    other_des = fields.Text(string='Other Description')

    @api.constrains('percentage_ids',)
    def check_percentages(self):
        if self.related_to in ('project', 'business_dev'):
            totals = 0
            for rec in self.percentage_ids:
                totals += rec.percentage
            if totals != 100:
                raise exceptions.ValidationError(_("Total distribution of percentages must be 100%!"))

    @api.multi
    def approve_expense_sheets(self):
        super(HrExpenseSheet, self).approve_expense_sheets()
        if self.related_to in ('project', 'business_dev'):
            for rec in self.percentage_ids:
                analytic_line_id = self.env['account.analytic.line'].create({
                    'name': "Expense For %s" % self.employee_id.name,
                    'project_id': rec.project_id.id or False,
                    'account_id': rec.project_id.analytic_account_id.id or rec.lead_id.analytic_id.id,
                    'unit_amount': 1,
                    'user_id': self.employee_id.user_id.id,
                    'date': fields.Date.today(),
                    'partner_id': self.employee_id.user_id.partner_id.id,
                })
                analytic_line_id.write({'amount': self.total_amount * (rec.percentage / 100)})
        else:
            config_id = self.env['res.config.settings'].search([('general_analytic_account', '!=', False)], limit=1, order='id desc')
            if config_id.general_analytic_account.id:
                self.env['account.analytic.line'].create({
                    'name': "Expense For %s" % self.employee_id.name,
                    'account_id': config_id.general_analytic_account.id,
                    'amount': self.total_amount,
                    'unit_amount': 1,
                    'user_id': self.employee_id.user_id.id,
                    'date': fields.Date.today(),
                    'partner_id': self.employee_id.user_id.partner_id.id,
                })
            else:
                raise UserError(_('Please set general analytic account from settings.'))

    @api.onchange('related_to')
    def _onchange_related_to(self):
        self.percentage_ids = False


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    related_to = fields.Selection([('project', 'Project'),
                                   ('business_dev', 'Business Development'),
                                   ('other', 'Other')], string='Related To', track_visibility='always')
    percentage_ids = fields.One2many('projects.travels', 'expense_id', string='Projects/Leads',
                                     track_visibility='always')
    other_des = fields.Text(string='Other Description')

    @api.constrains('percentage_ids',)
    def check_percentages(self):
        if self.related_to in ('project', 'business_dev'):
            totals = 0
            for rec in self.percentage_ids:
                totals += rec.percentage
            if totals != 100:
                raise exceptions.ValidationError(_("Total distribution of percentages must be 100%!"))

    @api.onchange('related_to')
    def _onchange_related_to(self):
        self.percentage_ids = False

    @api.multi
    def action_submit_expenses(self):
        if any(expense.state != 'draft' or expense.sheet_id for expense in self):
            raise UserError(_("You cannot report twice the same line!"))
        if len(self.mapped('employee_id')) != 1:
            raise UserError(_("You cannot report expenses for different employees in the same report."))

        todo = self.filtered(lambda x: x.payment_mode=='own_account') or self.filtered(lambda x: x.payment_mode=='company_account')
        return {
            'name': _('New Expense Report'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.expense.sheet',
            'target': 'current',
            'context': {
                'default_expense_line_ids': todo.ids,
                'default_employee_id': self[0].employee_id.id,
                'default_other_des': self[0].other_des,
                'default_percentage_ids': [(6, 0, self[0].percentage_ids.ids)],
                'default_related_to': self[0].related_to,
                'default_name': todo[0].name if len(todo) == 1 else ''
            }
        }


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.depends('line_ids', 'state')
    def _compute_salary_amount(self):
        for rec in self:
            line = rec.line_ids.filtered(lambda x: x.code == 'NET')
            rec.total_salary = line.total

    include_expense = fields.Boolean('Include Expense')
    include_vacations = fields.Boolean('Include Vacations')
    total_salary = fields.Float('Salary Amount', store=True, compute='_compute_salary_amount')

    @api.multi
    def action_payslip_done(self):
        res = super(HrPayslip, self).action_payslip_done()
        if self.input_line_ids:
            for line in self.input_line_ids:
                if line.expense_id:
                    line.expense_id.state = 'done'
                if line.awarded_id:
                    line.awarded_id.is_paid = True
                if line.per_diem_id:
                    line.per_diem_id.state = 'paid'
                if line.leave_id:
                    line.leave_id.is_deducted = True

        return res

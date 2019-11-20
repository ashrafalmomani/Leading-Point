# -*- coding: utf-8 -*-

from odoo import models, api, fields


class PayrollCustom(models.Model):
    _inherit = 'hr.payslip.run'

    include_expense = fields.Boolean('Include Expense')
    include_vacations = fields.Boolean('Include Vacations')

    @api.multi
    def deduct_unpaid_vacations(self):
        for payslip in self.slip_ids:
            for leave in self.env['hr.leave'].search([('employee_id', '=', payslip.employee_id.id),
                                                      ('state', 'in', ('validate', 'validate1')),
                                                      ('is_deducted', '=', False),
                                                      ('include_in_salary', '=', True),
                                                      ('holiday_status_id.unpaid', '=', True)]):
                holiday_name = 'Unpaid Leave (' + str(leave.request_date_from) + ' TO ' + str(leave.request_date_to) + ')'
                amount = -(payslip.employee_id.contract_id.wage / 30) * leave.number_of_days
                payslip.input_line_ids.create({'payslip_id': payslip.id,
                                               'name': holiday_name,
                                               'code': 'Unpaid',
                                               'amount': amount,
                                               'contract_id': payslip.employee_id.contract_id.id,
                                               'leave_id': leave.id})
            payslip.compute_sheet()
            self.include_vacations = True

    @api.multi
    def include_expenses(self):
        for payslip in self.slip_ids:
            for awarded in self.env['hr.awarded.days'].search([('employee_id', '=', payslip.employee_id.id),
                                                               ('state', '=', 'hr_approved'),
                                                               ('is_paid', '=', False)]):
                payslip.input_line_ids.create({'payslip_id': payslip.id,
                                               'name': awarded.name,
                                               'code': 'AwardedDays',
                                               'amount': (payslip.employee_id.contract_id.wage / 30 / 8) * awarded.total_hour,
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

            for per_diem in self.env[''].search([('employee_id', '=', payslip.employee_id.id),
                                                              ('state', '=', 'not_paid'),
                                                              ('from_date', '>=', payslip.date_from),
                                                              ('to_date', '<=', payslip.date_to)]):
                payslip.input_line_ids.create({'payslip_id': payslip.id,
                                               'name': per_diem.name,
                                               'code': 'PerDiem',
                                               'amount': per_diem.amount,
                                               'contract_id': payslip.employee_id.contract_id.id,
                                               'per_diem_id': per_diem.id})
            payslip.compute_sheet()
            self.include_expense = True


class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    leave_id = fields.Many2one('hr.leave', string='Leave')
    awarded_id = fields.Many2one('hr.awarded.days', string='Awarded Days')
    expense_id = fields.Many2one('hr.expense.sheet', string='Expense')


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    include_in_salary = fields.Boolean(string='Include In Salary', default=True)


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

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
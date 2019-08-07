# -*- coding: utf-8 -*-

from odoo import models, api


class PayrollCustom(models.Model):
    _inherit = 'hr.payslip.run'

    @api.multi
    def deduct_unpaid_vacations(self):
        for payslip in self.slip_ids:
            for item in self.env['hr.leave'].search([('employee_id', '=', payslip.employee_id.id),
                                                     ('state', '=', 'validate'),
                                                     ('is_deducted', '=', False),
                                                     ('include_in_salary', '=', True),
                                                     ('holiday_status_id.unpaid', '=', True)]):
                holidayname = 'Unpaid Leave ( ' + str(item.request_date_from) + ' - ' + str(item.request_date_to) + ' )'
                amount = -(payslip.employee_id.contract_id.wage / 30) * item.number_of_days
                exist = False
                for input in payslip.input_line_ids:
                    if input.name == holidayname:
                        exist = True
                if not exist:
                    payslip.input_line_ids.create(
                        {'payslip_id': payslip.id, 'name': holidayname, 'code': item.holiday_status_id.name, 'amount': amount, 'contract_id': payslip.employee_id.contract_id.id})
                item.is_deducted = True
            payslip.compute_sheet()

    @api.multi
    def include_expenses(self):
        for payslip in self.slip_ids:
            for item in self.env['hr.awarded.days'].search([('employee_id', '=', payslip.employee_id.id),
                                                            ('state', '=', 'hr_approved'),
                                                            ('is_paid', '=', False)]):
                name = item.name
                amount = (payslip.employee_id.contract_id.wage / 30) * item.total_hour
                exist = False
                for input in payslip.input_line_ids:
                    if input.name == name:
                        exist = True
                if not exist:
                    payslip.input_line_ids.create(
                        {'payslip_id': payslip.id, 'name': name, 'code': 'Awarded Days', 'amount': amount, 'contract_id': payslip.employee_id.contract_id.id})

            for item in self.env['hr.travel'].search([('employee', '=', payslip.employee_id.id),
                                                      ('state', '=', 'hr_approved'),
                                                      ('trip_status', '=', 'open')]):
                name = item.name
                amount = (payslip.employee_id.contract_id.wage / 30) * item.total_hour
                exist = False
                for input in payslip.input_line_ids:
                    if input.name == name:
                        exist = True
                if not exist:
                    payslip.input_line_ids.create(
                        {'payslip_id': payslip.id, 'name': name, 'code': 'Per Diem', 'amount': amount,
                         'contract_id': payslip.employee_id.contract_id.id})
            payslip.compute_sheet()

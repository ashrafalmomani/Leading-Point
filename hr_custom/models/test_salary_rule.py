# # -*- coding: utf-8 -*-
#
# from odoo import models, fields, api
#
#
# class SalaryRuleTest(models.Model):
#     _name = 'salary.rule.test'
#
#
#     @api.depends('result')
#     def action_calculate_salary(self):
#         rule = 9000/12
#         tax_level_amount = 5000/12
#         for rec in self:
#             if rec.married:
#                 total_exemption = rule * 2
#             else:
#                 total_exemption = rule
#
#             taxable_income = rec.basic_salary - total_exemption
#             percentage_num = int(taxable_income / tax_level_amount)
#
#             if percentage_num < 1:
#                 if taxable_income > 0 :
#                     tax_five_perc = taxable_income * 0.05
#                     total_tax = tax_five_perc
#                     rec.result = total_tax
#                 else:
#                     rec.result = 0.0
#
#             elif percentage_num == 1:
#                 tax_five_perc = tax_level_amount * 0.05
#                 last_tax_perc = taxable_income - tax_level_amount
#                 tax_ten_perc = last_tax_perc * 0.1
#                 total_tax = tax_five_perc + tax_ten_perc
#                 rec.result = total_tax
#
#             elif percentage_num == 2:
#                 tax_five_perc = tax_level_amount * 0.05
#                 tax_ten_perc = tax_level_amount * 0.1
#                 last_tax_perc = taxable_income - (tax_level_amount * 2)
#                 tax_fifteen_perc = last_tax_perc * 0.15
#                 total_tax = tax_five_perc + tax_ten_perc + tax_fifteen_perc
#                 rec.result = total_tax
#
#             elif percentage_num == 3:
#                 tax_five_perc = tax_level_amount * 0.05
#                 tax_ten_perc = tax_level_amount * 0.1
#                 tax_fifteen_perc = tax_level_amount * 0.15
#                 last_tax_perc = taxable_income - (tax_level_amount * 3)
#                 tax_twenty_perc = last_tax_perc * 0.20
#                 total_tax = tax_five_perc + tax_ten_perc + tax_fifteen_perc + tax_twenty_perc
#                 rec.result = total_tax
#
#             elif percentage_num == 4:
#                 tax_five_perc = tax_level_amount * 0.05
#                 tax_ten_perc = tax_level_amount * 0.1
#                 tax_fifteen_perc = tax_level_amount * 0.15
#                 tax_twenty_perc = tax_level_amount * 0.20
#                 last_tax_perc = taxable_income - (tax_level_amount * 4)
#                 tax_twenty_five_perc = last_tax_perc * 0.25
#                 total_tax = tax_five_perc + tax_ten_perc + tax_fifteen_perc + tax_twenty_perc + tax_twenty_five_perc
#                 rec.result = total_tax
#
#             elif percentage_num == 5:
#                 tax_five_perc = tax_level_amount * 0.05
#                 tax_ten_perc = tax_level_amount * 0.1
#                 tax_fifteen_perc = tax_level_amount * 0.15
#                 tax_twenty_perc = tax_level_amount * 0.20
#                 tax_twenty_five_perc = tax_level_amount * 0.25
#                 last_tax_perc = taxable_income - (tax_level_amount * 5)
#                 tax_thirty_perc = last_tax_perc * 0.30
#                 total_tax = tax_five_perc + tax_ten_perc + tax_fifteen_perc + tax_twenty_perc + tax_twenty_five_perc + tax_thirty_perc
#                 rec.result = total_tax
#
#             elif percentage_num == 6:
#                 tax_five_perc = tax_level_amount * 0.05
#                 tax_ten_perc = tax_level_amount * 0.1
#                 tax_fifteen_perc = tax_level_amount * 0.15
#                 tax_twenty_perc = tax_level_amount * 0.20
#                 tax_twenty_five_perc = tax_level_amount * 0.25
#                 tax_thirty_perc = tax_level_amount * 0.30
#                 total_tax = tax_five_perc + tax_ten_perc + tax_fifteen_perc + tax_twenty_perc + tax_twenty_five_perc + tax_thirty_perc
#                 rec.result = total_tax
#             else:
#                 rec.result = 0.0
#
#     basic_salary = fields.Float(string='Basic Salary')
#     single = fields.Boolean(string='Single')
#     married = fields.Boolean(string='Married')
#     result = fields.Float(string='Result', compute=action_calculate_salary)



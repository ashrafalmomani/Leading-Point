# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrLeave(models.Model):
    _inherit = "hr.leave"

    include_in_salary = fields.Boolean(string='Include In Salary', default=True)
    is_deducted = fields.Boolean(string='Is Deducted')
    project = fields.Many2one('project.project', string='Project')
    opportunities = fields.Many2one('crm.lead', string='Opportunities')
    unpaid_leave = fields.Boolean('Unpaid Leave', related='holiday_status_id.unpaid')
    working_on = fields.Selection([('project', 'Project'), ('opportunity', 'Opportunity')], string='Working On', track_visibility='always')
    salary = fields.Float('Salary', store=True)

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            wage = self.employee_id.contract_id.wage + self.employee_id.contract_id.salary_raise
            self.salary = wage

    @api.onchange('working_on')
    def _onchange_working_on(self):
        if self.working_on == 'project':
            self.opportunities = False
        elif self.working_on == 'opportunity':
            self.project = False
        else:
            self.project = False
            self.opportunities = False

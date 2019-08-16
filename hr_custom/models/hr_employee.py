# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HumanResourceCustom(models.Model):
    _inherit = "hr.employee"

    joining_date = fields.Date(string='Joining Date')
    arabic_name = fields.Char(string='Name in Arabic')
    current_contract_start = fields.Date(string='Current Contract Start', compute='compute_current_contract_start')
    document_ids = fields.One2many('document.line', 'employee_id', string='Document')
    user_check_tick = fields.Boolean(default=False)

    @api.multi
    def create_user(self):
        user_id = self.env['res.users'].create({'name': self.name, 'login': self.work_email})
        self.address_home_id = user_id.partner_id.id
        self.user_id = user_id.id
        self.user_check_tick = True

    @api.onchange('address_home_id')
    def user_checking(self):
        if self.address_home_id:
            self.user_check_tick = True
        else:
            self.user_check_tick = False

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

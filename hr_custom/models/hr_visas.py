# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HREmployeeVisas(models.Model):
    _name = "hr.visas"
    _description = 'Visas'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'travel_id'

    @api.model
    def _default_officer_user_id(self):
        return self.env['res.users'].search([('groups_id', 'in', self.env.ref('hr_custom.group_visa_officer').id)],
                                            limit=1,
                                            order="id desc")

    def _default_manager_id(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])

    type = fields.Selection([('depend_on_travel', 'Depend On Travel'), ('just_visa', 'Just Visa')], string='Type', track_visibility='always')
    travel_id = fields.Many2one('hr.travel', string='Travel', track_visibility='always', domain="[('state', '=', 'hr_approved'), ('visa_required', '=', True)]")
    employee_id = fields.Many2one('hr.employee', string='Employee', track_visibility='always')
    country = fields.Many2one('res.country', string='Country', track_visibility='always')
    valid_form = fields.Date(string='Valid From', track_visibility='always')
    valid_till = fields.Date(string='Valid Till', track_visibility='always')
    active = fields.Boolean('Active', default=True)
    multiple_entry = fields.Boolean(string='Is Multiple Entry', track_visibility='always')
    linked = fields.Boolean(string='Linked', default=False)
    analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    visa = fields.Binary(string='UPLOAD YOUR FILE', track_visibility='always')
    cost = fields.Float(string='Cost', track_visibility='always')
    officer_user_id = fields.Many2one('res.users', default=_default_officer_user_id)
    project_manager = fields.Many2one('hr.employee', string='Project Manager', default=_default_manager_id, track_visibility='always')
    state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted'),
                              ('issued', 'Issued'), ('rejected', 'Rejected'), ('cancelled', 'Cancelled')],
                             default='draft', store=True, track_visibility='always')

    @api.multi
    def action_visa_submitted(self):
        notification = {
            'activity_type_id': self.env.ref('hr_custom.notification_after_visa_submitted').id,
            'res_id': self.id,
            'res_model_id': self.env['ir.model'].search([('model', '=', 'hr.visas')], limit=1).id,
            'icon': 'fa-pencil-square-o',
            'date_deadline': fields.Date.today(),
            'user_id': self.officer_user_id.id,
            'note': 'Request For Visa'
        }
        self.env['mail.activity'].create(notification)

        template_id = self.env.ref('hr_custom.email_after_visa_submitted')
        composer = self.env['mail.compose.message'].sudo().with_context({
            'default_composition_mode': 'mass_mail',
            'default_notify': False,
            'default_model': 'hr.visas',
            'default_res_id': self.id,
            'default_template_id': template_id.id,
        }).create({})
        values = composer.onchange_template_id(template_id.id, 'mass_mail', 'hr.visas', self.id)['value']
        composer.write(values)
        composer.send_mail()

        self.state = 'submitted'

    @api.multi
    def action_visa_issued(self):
        if self.type == 'depend_on_travel':
            projects = []
            if self.travel_id.reason_for_travel in ('project', 'business_dev'):
                for rec in self.travel_id.percentage_ids:
                    projects.append(self.cost * (rec.percentage / 100))
                    self.env['account.analytic.line'].create({
                        'name': "Visa for (%s) Travel" % self.travel_id.name,
                        'project_id': rec.project_id.id or False,
                        'account_id': rec.project_id.analytic_account_id.id or rec.lead_id.analytic_id.id,
                        'amount': projects[0],
                        'unit_amount': 1,
                        'user_id': self.travel_id.employee.user_id.id,
                        'date': fields.Date.today(),
                        'partner_id': self.travel_id.employee.user_id.partner_id.id,
                    })
                    projects = []
            else:
                self.env['account.analytic.line'].create({
                    'name': "Visa for (%s) Travel" % self.travel_id.name,
                    'account_id': self.travel_id.analytic_id.id,
                    'amount': self.cost,
                    'unit_amount': 1,
                    'user_id': self.travel_id.employee.user_id.id,
                    'date': fields.Date.today(),
                    'partner_id': self.travel_id.employee.user_id.partner_id.id,
                })

        notification = {
            'activity_type_id': self.env.ref('hr_custom.notification_after_visa_issued').id,
            'res_id': self.id,
            'res_model_id': self.env['ir.model'].search([('model', '=', 'hr.visas')], limit=1).id,
            'icon': 'fa-pencil-square-o',
            'date_deadline': fields.Date.today(),
            'user_id': self.project_manager.id,
            'note': 'The request for visa is approved'
        }
        self.env['mail.activity'].create(notification)

        template_id = self.env.ref('hr_custom.email_after_visa_approved')
        composer = self.env['mail.compose.message'].sudo().with_context({
            'default_composition_mode': 'mass_mail',
            'default_notify': False,
            'default_model': 'hr.visas',
            'default_res_id': self.id,
            'default_template_id': template_id.id,
        }).create({})
        values = composer.onchange_template_id(template_id.id, 'mass_mail', 'hr.visas', self.id)['value']
        composer.write(values)
        composer.send_mail()

        self.state = 'issued'

    @api.multi
    def action_visa_with_travel(self):
        if self.type == 'depend_on_travel':
            projects = []
            if self.travel_id.reason_for_travel in ('project', 'business_dev'):
                for rec in self.travel_id.percentage_ids:
                    projects.append(self.cost * (rec.percentage / 100))
                    self.env['account.analytic.line'].create({
                        'name': "Visa for (%s) Travel" % self.travel_id.name,
                        'project_id': rec.project_id.id or False,
                        'account_id': rec.project_id.analytic_account_id.id or rec.lead_id.analytic_id.id,
                        'amount': projects[0],
                        'unit_amount': 1,
                        'user_id': self.travel_id.employee.user_id.id,
                        'date': fields.Date.today(),
                        'partner_id': self.travel_id.employee.user_id.partner_id.id,
                    })
                    projects = []
            else:
                self.env['account.analytic.line'].create({
                    'name': "Visa for (%s) Travel" % self.travel_id.name,
                    'account_id': self.travel_id.analytic_id.id,
                    'amount': self.cost,
                    'unit_amount': 1,
                    'user_id': self.travel_id.employee.user_id.id,
                    'date': fields.Date.today(),
                    'partner_id': self.travel_id.employee.user_id.partner_id.id,
                })
            self.linked = True

    @api.multi
    def create_analytic_cost_in_visa(self):
        for rec in self.env['hr.visas'].search([('state', '=', 'issued'), ('type', '=', 'just_visa')]):
            if fields.Date.today() > rec.valid_till:
                self.env['account.analytic.line'].create({
                    'name': "Visa for (%s) Employee" % rec.employee_id.name,
                    'project_id': False,
                    'account_id': rec.analytic_id.id,
                    'amount': rec.cost,
                    'unit_amount': 1,
                    'user_id': self.employee_id.user_id.id,
                    'date': fields.Date.today(),
                    'partner_id': self.employee_id.user_id.partner_id.id,
                })

    @api.multi
    def check_active_in_visa(self):
        for rec in self.env['hr.visas'].search([('state', '=', 'issued'), ('active', '=', True)]):
            if fields.Date.today() > rec.valid_till:
                rec.active = False

    @api.multi
    def action_visa_rejected(self):
        self.state = 'rejected'

    @api.multi
    def action_cancel(self):
        self.state = 'cancelled'

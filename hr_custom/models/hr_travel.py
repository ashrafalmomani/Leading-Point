# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import timedelta


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    per_diem_amount = fields.Float('Per Diem Amount')
    awarded_account_id = fields.Many2one('account.account', string='Awarded Days Account')
    awarded_days_journal_id = fields.Many2one('account.journal', string='Journal')

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['per_diem_amount'] = self.search([], limit=1, order='id desc').per_diem_amount
        res['awarded_account_id'] = self.search([], limit=1, order='id desc').awarded_account_id.id
        res['awarded_days_journal_id'] = self.search([], limit=1, order='id desc').awarded_days_journal_id.id
        return res


class EmployeeContract(models.Model):
    _inherit = 'hr.contract'

    @api.model
    def _get_default_user(self):
        return self.env['res.users'].search([('groups_id', 'in', self.env.ref('hr.group_hr_manager').id)], limit=1, order="id desc")

    salary_raise = fields.Float(string='Salary Raise', track_visibility='always')
    manager_user_id = fields.Many2one('res.users', string='HR Manager', default=_get_default_user)

    @api.multi
    def end_of_trial_period_email(self):
        contracts = self.env['hr.contract'].search([('state', '=', 'open'), ('trial_date_end', '>', fields.Date.today())])
        user_id = self.env['res.users'].search([('groups_id', 'in', self.env.ref('hr.group_hr_manager').id)], limit=1, order="id desc")
        for rec in contracts:
            before_two_week = rec.trial_date_end - timedelta(days=14)
            before_one_week = rec.trial_date_end - timedelta(days=7)
            if before_two_week == fields.Date.today():
                reminder_notification = {
                    'activity_type_id': self.env.ref('hr_custom.mail_activity_reminder_notification').id,
                    'res_id': rec.id,
                    'res_model_id': self.env['ir.model'].search([('model', '=', 'hr.contract')], limit=1).id,
                    'icon': 'fa-pencil-square-o',
                    'date_deadline': rec.trial_date_end,
                    'user_id': user_id.id,
                    'note': 'End Of Trial Period After Two Week'
                }
                self.env['mail.activity'].create(reminder_notification)

                template_id = self.env.ref('hr_custom.end_of_trial_period_before_two_week')
                composer = self.env['mail.compose.message'].sudo().with_context({
                    'default_composition_mode': 'mass_mail',
                    'default_notify': False,
                    'default_model': 'hr.contract',
                    'default_res_id': rec.id,
                    'default_template_id': template_id.id,
                }).create({})
                values = composer.onchange_template_id(template_id.id, 'mass_mail', 'hr.contract', rec.id)['value']
                composer.write(values)
                composer.send_mail()

            elif before_one_week == fields.Date.today():
                reminder_notification = {
                    'activity_type_id': self.env.ref('hr_custom.mail_activity_reminder_notification').id,
                    'res_id': rec.id,
                    'res_model_id': self.env['ir.model'].search([('model', '=', 'hr.contract')], limit=1).id,
                    'icon': 'fa-pencil-square-o',
                    'date_deadline': rec.trial_date_end,
                    'user_id': user_id.id,
                    'note': 'End Of Trial Period After One Week'
                }
                self.env['mail.activity'].create(reminder_notification)

                template_id = self.env.ref('hr_custom.end_of_trial_period_before_one_week')
                composer = self.env['mail.compose.message'].sudo().with_context({
                    'default_composition_mode': 'mass_mail',
                    'default_notify': False,
                    'default_model': 'hr.contract',
                    'default_res_id': rec.id,
                    'default_template_id': template_id.id,
                }).create({})
                values = composer.onchange_template_id(template_id.id, 'mass_mail', 'hr.contract', rec.id)['value']
                composer.write(values)
                composer.send_mail()

    @api.multi
    def add_raise_to_wage_every_first_year(self):
        contracts = self.env['hr.contract'].search([('state', '=', 'open')])
        for rec in contracts:
            rec.wage += rec.salary_raise
            rec.salary_raise = 0.0


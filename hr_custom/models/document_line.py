# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta


class DocumentLine(models.Model):
    _name = "document.line"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _get_default_user_manager(self):
        return self.env['res.users'].search([('groups_id', 'in', self.env.ref('hr.group_hr_manager').id)], limit=1,
                                            order="id desc")

    name = fields.Char(string='Name')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    expiry_date = fields.Date(string='Expiry Date')
    alert_before = fields.Integer(string='Alert Before(Months)')
    alert = fields.Boolean(string='Alert')
    document = fields.Binary(string='Document')
    document_type = fields.Many2one('document.employee', string='Document Type')
    manager_user_id = fields.Many2one('res.users', string='HR Manager', default=_get_default_user_manager)

    @api.multi
    def alert_before_expiry_date_document(self):
        documents = self.env['document.line'].search(
            [('alert', '=', True), ('expiry_date', '>', fields.Date.today())])
        user_id = self.env['res.users'].search([('groups_id', 'in', self.env.ref('hr.group_hr_manager').id)], limit=1,
                                               order="id desc")
        for rec in documents:
            if rec.alert_before:
                alerts = rec.expiry_date - relativedelta(months=rec.alert_before)
                if alerts == fields.Date.today():
                    alert_notification = {
                        'activity_type_id': self.env.ref('hr_custom.mail_activity_alert_before_notification').id,
                        'res_id': rec.id,
                        'res_model_id': self.env['ir.model'].search([('model', '=', 'document.line')], limit=1).id,
                        'icon': 'fa-pencil-square-o',
                        'date_deadline': rec.expiry_date,
                        'user_id': user_id.id,
                        'note': 'The Expiry Date For (' + rec.employee_id.name + ') Document After (' + str(rec.alert_before) + ') Months'
                    }
                    self.env['mail.activity'].create(alert_notification)

                    template_id = self.env.ref('hr_custom.alert_email_before_expiry_date_document')
                    composer = self.env['mail.compose.message'].sudo().with_context({
                        'default_composition_mode': 'mass_mail',
                        'default_notify': False,
                        'default_model': 'document.line',
                        'default_res_id': rec.id,
                        'default_template_id': template_id.id,
                    }).create({})
                    values = composer.onchange_template_id(template_id.id, 'mass_mail', 'document.line', rec.id)['value']
                    composer.write(values)
                    composer.send_mail()


class EmployeeDocument(models.Model):
    _name = "document.employee"

    name = fields.Char(string='Name')

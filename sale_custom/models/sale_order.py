# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _get_user_receive_email(self):
        return self.env['res.users'].search([('groups_id', 'in', self.env.ref('sale_custom.group_email_to_account_manager').id)],
                                            limit=1,
                                            order="id desc")

    payment_ids = fields.One2many('payment.schedule', 'payment_id', string='Payment Schedule')
    user_receive_email = fields.Many2one('res.users', string='Account Manager receive email', default=_get_user_receive_email)
    is_boolean = fields.Boolean('Boolean', default=False)

    @api.multi
    def action_confirm(self):
        if self.client_order_ref == False:
            raise UserError(_("Please, Fill Customer Reference."))
        super(SaleOrder, self).action_confirm()

        # template_id = self.env.ref('sale_custom.email_to_account_manager')
        # composer = self.env['mail.compose.message'].sudo().with_context({
        #     'default_composition_mode': 'mass_mail',
        #     'default_notify': False,
        #     'default_model': 'sale.order',
        #     'default_res_id': self.id,
        #     'default_template_id': template_id.id,
        # }).create({})
        # values = composer.onchange_template_id(template_id.id, 'mass_mail', 'sale.order', self.id)['value']
        # composer.write(values)
        # composer.send_mail()

    @api.multi
    def create_project(self):
        return {
            'name': _('Project'),
            'domain': [('sale_order_id', '=', self.id)],
            'res_model': 'project.project',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_type': 'form',
            'view_mode': 'kanban,form',
            'target': 'current'}

    @api.multi
    def action_create_project(self):
        for order in self:
            name = order.name
            analytic = self.env['account.analytic.account'].create({
                'name': name,
                'code': order.client_order_ref,
                'company_id': order.company_id.id,
                'partner_id': order.partner_id.id
            })
            order.analytic_account_id = analytic

            values = {
                'name': '%s - %s' % (order.client_order_ref, order.name) if order.client_order_ref else order.name,
                'allow_timesheets': True,
                'analytic_account_id': analytic.id,
                'sale_order_id': order.id,
                'partner_id': order.partner_id.id,
                'active': True,
                'user_id': False,
            }
            if values:
                project_id = self.env['project.project'].create(values)
                order.is_boolean = True

        return {
            'name': _('Project'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.project',
            'target': 'current',
            'res_id': project_id.id,
            'view_mode': 'form',
        }


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    mask_name = fields.Many2one('child.product', string='Child Name', domain="[('product_id', '=', product_id )]")

    @api.onchange('mask_name')
    def _onchange_description(self):
        if self.mask_name:
            self.name = self.mask_name.mask_name


class PaymentSchedule(models.Model):
    _name = 'payment.schedule'

    payment_id = fields.Many2one('sale.order', string='Payment Schedule')
    description = fields.Char(string='Description')
    percentage = fields.Float(string='Percentage')

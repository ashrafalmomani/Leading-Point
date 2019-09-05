# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    payment_ids = fields.One2many('payment.schedule', 'payment_id', string='Payment Schedule')
    is_boolean = fields.Boolean('Boolean', default=False)

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
                'name': '%s - %s' % (self.client_order_ref, self.name) if self.client_order_ref else self.name,
                'allow_timesheets': True,
                'analytic_account_id': analytic.id,
                'partner_id': self.partner_id.id,
                'sale_order_id': self.id,
                'active': True,
            }
            if values:
                self.env['project.project'].create(values)
                self.is_boolean = True


class PaymentSchedule(models.Model):
    _name = 'payment.schedule'

    payment_id = fields.Many2one('sale.order', string='Payment Schedule')
    description = fields.Char(string='Description')
    percentage = fields.Float(string='Percentage')

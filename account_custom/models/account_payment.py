# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PaymentMethods(models.Model):
    _inherit = "account.payment"

    bank_name = fields.Many2one('res.bank', string='Bank')
    cheque_number = fields.Char(string="Check Number", copy=False)


class PartnerTab(models.Model):
    _inherit = "res.partner"

    partner_ids = fields.One2many('partner.type.info', 'partner_id', string='Partner Document')


class PartnerTabInfo(models.Model):
    _name = "partner.type.info"

    partner_id = fields.Many2one('res.partner', string='Partner Document')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    type = fields.Many2one('partner.type.tab', string='Type')
    description = fields.Text(string='Description')
    attachment = fields.Binary(string='Attachment')


class PartnerTabType(models.Model):
    _name = "partner.type.tab"

    name = fields.Char()

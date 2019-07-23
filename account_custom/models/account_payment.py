# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PaymentMethods(models.Model):
    _inherit = "account.payment"

    bank_name = fields.Many2one('res.bank', 'Bank')
    cheque_number = fields.Char(string="Check Number", copy=False)


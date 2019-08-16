# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountAsset(models.Model):
    _inherit = 'account.asset.asset'

    is_tracked = fields.Boolean("Is tracked?")

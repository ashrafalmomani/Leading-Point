# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class DocumentIrAttachment(models.Model):
    _inherit = "ir.attachment"

    expiry_date = fields.Date(string='Expiry Date')
    document_id = fields.Many2one('hr.employee', string='Document')
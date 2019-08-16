# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class DocumentLine(models.Model):
    _name = "document.line"

    name = fields.Char(string='Name')
    expiry_date = fields.Date(string='Expiry Date')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    document = fields.Binary(string='Document')
    document_type = fields.Selection([('id', 'ID'), ('passport', 'Passport')], string='Document Type')

# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductTemplateCustom(models.Model):
    _inherit = 'product.template'

    mask_ids = fields.One2many('child.product', 'product_id', string='Child Name')


class MaskName(models.Model):
    _name = 'mask.name'
    _rec_name = 'mask_name'

    mask_name = fields.Char(string='Child Name')


class ChildProduct(models.Model):
    _name = 'child.product'
    _rec_name = 'child_id'

    child_id = fields.Many2one('mask.name', string='Child Name')
    product_id = fields.Many2one('product.template', string='Product')

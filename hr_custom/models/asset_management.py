# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AssetManagement(models.Model):
    _name = 'asset.management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'The Asset Management module'

    name = fields.Char("Name", required=True, copy=False, index=True, default='New', track_visibility='always')
    related_assets = fields.Many2one('account.asset.asset', string="Related Asset", track_visibility='always')
    serial_num = fields.Char("Serial Number", required=True, track_visibility='always')
    mac_address = fields.Char("MAC Address", track_visibility='always')
    is_assigned_to_employee = fields.Boolean("Is assigned", track_visibility='always')
    assigned_employee = fields.Many2one('hr.employee', string="Assigned Employee", track_visibility='always')
    notes = fields.Text("Notes", track_visibility='always')
    is_related_asset_tracked = fields.Boolean("Is tracked", track_visibility='always')
    state = fields.Selection([("unassign", "Unassign"), ("assign", "Assign"), ("deprecated", "Deprecated")], default='unassign', track_visibility='always')

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('asset.management') or '/'
        return super(AssetManagement, self).create(vals)


    @api.multi
    def deprecated_action(self):
        self.write({'state': 'deprecated'})

    @api.multi
    def assign_action(self):
        self.write({'state': 'assign'})

    @api.multi
    def unassign_action(self):
        self.write({'state': 'unassign'})

    @api.onchange('is_related_asset_tracked')
    def onchange_is_related_asset_tracked(self):
        if self.is_related_asset_tracked:
            self.env['account.asset.asset'].write({'is_tracked': self.is_related_asset_tracked})


class AccountAsset(models.Model):
    _inherit = 'account.asset.asset'

    is_tracked = fields.Boolean("Is tracked?")

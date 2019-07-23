# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResUsersInherit(models.Model):
    _inherit = 'hr.employee'

    user_check_tick = fields.Boolean(default=False)

    @api.multi
    def create_user(self):
        user_id = self.env['res.users'].create({'name': self.name, 'login': self.work_email})
        self.address_home_id = user_id.partner_id.id
        self.user_id = user_id.id
        self.user_check_tick = True

    @api.onchange('address_home_id')
    def user_checking(self):
        if self.address_home_id:
            self.user_check_tick = True
        else:
            self.user_check_tick = False


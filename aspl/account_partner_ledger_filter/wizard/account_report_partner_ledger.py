# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountPartnerLedger(models.TransientModel):
    _inherit = "account.report.partner.ledger"

    partner_ids = fields.Many2many('res.partner', 'partner_ledger_partner_rel', 'id', 'partner_id', string='Partners')

    def generate_partner_ledger(self, data):
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['partner_ids', 'date_from', 'date_to', 'journal_ids', 'display_account', 'target_move', 'reconciled', 'result_selection','amount_currency'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')
        datas = {
            'ids': self._ids,
            'docs': self._ids,
            'model': 'account.report.partner.ledger',
            'form': data['form'],
        }
        return self.env.ref('aspl_accounting_report.report_partner_ledger').report_action(self, data=datas)

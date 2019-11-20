# -*- coding: utf-8 -*-

from odoo import models, api
from datetime import date
from dateutil.relativedelta import relativedelta


class RunPerDiem(models.TransientModel):
    _name = "run.per.diem"
    _description = 'Run Per Diem'

    @api.multi
    def calculate_per_diem(self):
        tickets = self.env['hr.tickets'].search([('state', '=', 'issued')])
        for ticket in tickets:
            if ticket.state != 'closed':
                if not ticket.per_diem_count:
                    first_day = ticket.new_departure_date
                    last_day = first_day + relativedelta(day=1, months=+1, days=-1)
                    diff_day = (last_day - first_day).days
                else:
                    today = date.today()
                    first_day = date(today.year, today.month, 1)
                    first_day_in_next_month = first_day + relativedelta(months=1)
                    last_day = first_day_in_next_month + relativedelta(days=-1)
                    if last_day > ticket.new_return_date:
                        last_day = ticket.new_return_date
                    diff_day = (last_day - first_day).days

            elif ticket.state == 'closed':
                if ticket.per_diem_count:
                    today = date.today()
                    first_day = date(today.year, today.month, 1)
                    last_day = ticket.new_return_date
                    diff_day = (last_day - first_day).days if last_day > first_day else 1
                else:
                    first_day = ticket.from_date
                    last_day = ticket.new_return_date
                    diff_day = (last_day - first_day).days

            if diff_day > 0:
                perdiem_amount = self.env['res.config.settings'].search([('per_diem_amount', '>', '0.0')], limit=1, order='id desc').per_diem_amount
                amount = (perdiem_amount * 0.708) * diff_day
                per_diem = self.env['per.diem.line'].create({'ticket_id': ticket.id,
                                                             'employee_id': ticket.employee_id.id,
                                                             'contract_id': ticket.employee_id.contract_id.id,
                                                             'amount': amount,
                                                             'from_date': first_day,
                                                             'to_date': last_day,
                                                             'state': 'not_paid'})
                print(per_diem)

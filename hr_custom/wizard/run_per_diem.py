# -*- coding: utf-8 -*-

from odoo import models, api
from datetime import date
from dateutil.relativedelta import relativedelta


class RunPerDiem(models.TransientModel):
    _name = "run.per.diem"
    _description = 'Run Per Diem'

    @api.multi
    def calculate_per_diem(self):
        travels = self.env['hr.travel'].search([('state', '=', 'hr_approved')])
        for travel in travels:
            if travel.trip_status == 'open':
                if not travel.per_diem_count:
                    first_day = travel.from_date
                    last_day = first_day + relativedelta(day=1, months=+1, days=-1)
                    diff_day = (last_day - first_day).days
                else:
                    today = date.today()
                    first_day = date(today.year, today.month, 1)
                    first_day_in_next_month = first_day + relativedelta(months=1)
                    last_day = first_day_in_next_month + relativedelta(days=-1)
                    if last_day > travel.to_date:
                        last_day = travel.to_date
                    diff_day = (last_day - first_day).days

            elif travel.trip_status == 'closed':
                if travel.per_diem_count:
                    today = date.today()
                    first_day = date(today.year, today.month, 1)
                    last_day = travel.to_date
                    diff_day = (last_day - first_day).days if last_day > first_day else 1
                else:
                    first_day = travel.from_date
                    last_day = travel.to_date
                    diff_day = (last_day - first_day).days

            if travel.trip_status in ('open', 'closed') and diff_day > 0:
                amount = (travel.employee.contract_id.per_diem_amount * 0.708) * diff_day
                per_diem = self.env['per.diem.line'].create({'travel_id': travel.id,
                                                             'employee_id': travel.employee.id,
                                                             'contract_id': travel.employee.contract_id.id,
                                                             'amount': amount,
                                                             'from_date': first_day,
                                                             'to_date': last_day,
                                                             'state': 'not_paid'})
                print(per_diem)

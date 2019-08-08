# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from datetime import datetime


class AppraisalCustom(models.Model):
    _name = 'hr.appraisal'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'er_seq'

    er_seq = fields.Char(string='ER Number', required=True, copy=False, default='New', track_visibility='always')
    employee_id = fields.Many2one('hr.employee', string='Employee', track_visibility='always')
    date_from = fields.Date(string='Date From', track_visibility='always')
    date_to = fields.Date(string='Date To', track_visibility='always')
    score_perc = fields.Float(string='Score Percantage', track_visibility='always')
    extra_point = fields.Float(string='Extra Points', track_visibility='always')
    total_score = fields.Float(string='Total Score', track_visibility='always')
    performance_level = fields.Char(string='Performance Level', track_visibility='always')
    job_id = fields.Many2one('hr.job', string='Job Position', track_visibility='always')
    salary = fields.Float(string='Salary', track_visibility='always')
    salary_raise = fields.Char(string='Salary Raise', track_visibility='always')
    next_review = fields.Date(string='Next Review Date', track_visibility='always')

    @api.model
    def create(self, vals):
        er_seq = self.env['ir.sequence'].next_by_code('hr.appraisal') or '/'
        vals.update({'er_seq': er_seq})
        return super(AppraisalCustom, self).create(vals)


class HRContracts(models.Model):
        _inherit = 'hr.contract'

        @api.multi
        def create_appraisal(self, vals):
            job_id = False
            appraisal_obj = self.env['hr.appraisal']
            start_date = datetime.strptime(vals['date_start'], '%Y-%m-%d')
            if 'job_id' in vals:
                job_id = self.env['hr.job'].browse(vals['job_id']).id
            appraisal_obj.sudo().create({
                'employee_id': vals['employee_id'],
                'job_id': job_id,
                'date_from': vals['date_start'],
                'date_to': start_date.date() + relativedelta(years=+1),
                'salary': vals['wage'],
            })

        @api.model
        def create(self, vals):
            self.create_appraisal(vals)
            return super(HRContracts, self).create(vals)

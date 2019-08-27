# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions
from dateutil.relativedelta import relativedelta
from datetime import datetime


class AppraisalCustom(models.Model):
    _name = 'hr.appraisal'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'er_seq'

    @api.one
    def _compute_total_score(self):
        total_scores = 0
        answers = self.env['survey.user_input'].search([('appraisal_id', '=', self.id)])
        for line in answers:
            total_scores += line.quizz_score
        if answers:
            average = total_scores / len(answers)
            self.score_perc = average
            self.total_score = average + self.extra_points

    @api.one
    def _compute_performance_level_next_review(self):
        level = self.env['appraisal.levels'].search([], limit=1, order='id DESC')
        if level:
            line = self.env['appraisal.form'].search([('appraisal_id', '=', level.id), ('score_from', '>=', self.total_score), ('score_to', '<=', self.total_score)])
            if len(line) > 1:
                raise exceptions.ValidationError(_("There are two line in appraisal levels has the same score"))
            else:
                self.performance_level = line.performance_level
                if self.performance_level in ('far_exceed', 'exceed', 'accomplish'):
                    self.next_review = self.date_to + relativedelta(months=+line.next_review)



    er_seq = fields.Char(string='ER Number', required=True, copy=False, default='New', track_visibility='always')
    employee_id = fields.Many2one('hr.employee', string='Employee', track_visibility='always')
    date_from = fields.Date(string='Date From', track_visibility='always')
    date_to = fields.Date(string='Date To', track_visibility='always')
    extra_points = fields.Float(string='Extra Points', track_visibility='always')
    score_perc = fields.Float(string='Score Percantage', track_visibility='always', compute='_compute_total_score')
    total_score = fields.Float(string='Total Score', track_visibility='always', compute='_compute_total_score')
    job_id = fields.Many2one('hr.job', string='Job Position', track_visibility='always')
    salary = fields.Float(string='Salary', track_visibility='always')
    salary_raise = fields.Char(string='Salary Raise', track_visibility='always')
    next_review = fields.Date(string='Next Review Date', track_visibility='always', compute='_compute_performance_level_next_review', readonly=False)
    survey_ids = fields.One2many('employee.survey', 'appraisal_id', string='Employee Survey')
    monthly_ids = fields.One2many('monthly.survey', 'monthly_id', string='Monthly Survey')
    answer_ids = fields.One2many('survey.user_input', 'appraisal_id', string='Answers')
    state = fields.Selection([('in_progress', 'In Progress'),
                              ('done', 'Done')], string='Status', default='in_progress', track_visibility='always')
    performance_level = fields.Selection([('far_exceed', 'Far Exceed'),
                                          ('exceed', 'Exceed'),
                                          ('accomplish', 'Accomplish'),
                                          ('poor', 'Poor'),
                                          ('under_perf', 'Under Performance')], compute=_compute_performance_level_next_review,
                                         string='Performance Level', track_visibility='always')

    @api.one
    @api.constrains('date_from', 'date_to')
    def check_dates(self):
        if self.date_from > self.date_to:
            raise exceptions.ValidationError(_("The date from cannot be greater than date to"))


    @api.model
    def create(self, vals):
        er_seq = self.env['ir.sequence'].next_by_code('hr.appraisal') or '/'
        vals.update({'er_seq': er_seq})
        return super(AppraisalCustom, self).create(vals)

    @api.multi
    def answers(self):
        return {
            'name': _('Answers'),
            'res_model': 'survey.user_input',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'domain': [('appraisal_id', '=', self.id)],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'target': 'current'}

    @api.multi
    def action_done(self):
        self.state = 'done'
        contract = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id), ('state', '=', 'open')], limit=1, order='id DESC')
        if contract:
            contract.salary_raise += self.salary_raise


class MonthlySurvey(models.Model):
    _name = 'monthly.survey'

    monthly_id = fields.Many2one('hr.appraisal', string='Monthly')
    description = fields.Text(string='Description')


class EmployeeSurvey(models.Model):
    _name = 'employee.survey'

    appraisal_id = fields.Many2one('hr.appraisal', string='Appraisal')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    response_id = fields.Many2one('survey.user_input', "Response", ondelete="set null", oldname="response")
    survey_id = fields.Many2one('survey.survey', string="Survey")

    @api.multi
    def action_start_survey(self):
        self.ensure_one()
        if not self.response_id:
            response = self.env['survey.user_input'].create({'survey_id': self.survey_id.id,
                                                             'partner_id': self.employee_id.user_id.partner_id.id,
                                                             'appraisal_id': self.appraisal_id.id})
            self.response_id = response.id
        else:
            response = self.response_id
        return self.survey_id.with_context(survey_token=response.token).action_start_survey()


class HRContracts(models.Model):
    _inherit = 'hr.contract'

    @api.multi
    def create_appraisal(self, vals):
        job_id = False
        appraisal_obj = self.env['hr.appraisal']
        start_date = datetime.strptime(vals['date_start'], '%Y-%m-%d')
        if 'job_id' in vals:
            survey_list = []
            job_id = self.env['hr.job'].browse(vals['job_id'])
            for survey in job_id.surveys_ids:
                values = {'employee_id': vals['employee_id'],
                          'survey_id': survey.id,
                          }
                survey_list.append([0, False, values])
        appraisal_obj.sudo().create({
            'employee_id': vals['employee_id'],
            'job_id': job_id.id,
            'date_from': vals['date_start'],
            'date_to': start_date.date() + relativedelta(years=+1),
            'salary': vals['wage'],
            'survey_ids': survey_list
        })

    @api.model
    def create(self, vals):
        self.create_appraisal(vals)
        return super(HRContracts, self).create(vals)

    @api.multi
    def add_salary_raise(self):
        contract = self.search([('state', '=', 'open')])
        for rec in contract:
            rec.wage += rec.salary_raise
            rec.salary_raise = 0.0


class HRJob(models.Model):
    _inherit = 'hr.job'

    surveys_ids = fields.Many2many('survey.survey', 'survey_job_rel', 'survey_id', 'job_id', string='Surveys')


class AppraisalId(models.Model):
    _inherit = 'survey.user_input'

    appraisal_id = fields.Many2one('hr.appraisal', string='Appraisal')


class AppraisalLevels(models.Model):
    _name = 'appraisal.levels'

    name = fields.Char(string='Name')
    appraisal_ids = fields.One2many('appraisal.form', 'appraisal_id', string='Appraisal Levels')


class AppraisalForm(models.Model):
    _name = 'appraisal.form'

    appraisal_id = fields.Many2one('appraisal.levels', string='Appraisal Levels', track_visibility='always')
    score_from = fields.Float(string='Score From', track_visibility='always')
    score_to = fields.Float(string='Score To', track_visibility='always')
    next_review = fields.Integer(string='Next Review After', track_visibility='always')
    performance_level = fields.Selection([('far_exceed', 'Far Exceed'),
                                          ('exceed', 'Exceed'),
                                          ('accomplish', 'Accomplish'),
                                          ('poor', 'Poor'),
                                          ('under_perf', 'Under Performance')],
                                         string='Performance Level', track_visibility='always')

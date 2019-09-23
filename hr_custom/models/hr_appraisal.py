# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions
from dateutil.relativedelta import relativedelta
from datetime import datetime
from odoo.exceptions import UserError


class AppraisalCustom(models.Model):
    _name = 'hr.appraisal'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'er_seq'

    @api.one
    def _compute_total_score(self):
        tot_in_months = 0.0
        total_num_of_month = 0.0
        for answer in self.answer_ids:
            count = 0
            question_result = 0.0
            for input in answer.user_input_line_ids:
                list_marks = []
                for label in input.question_id.labels_ids:
                    list_marks.append(label.quizz_mark)
                count += 1
                max_num = max(list_marks) if list_marks else 0
                question_result += input.quizz_mark / max_num if max_num > 0.0 else 1
            tot_question_result = question_result / count if count > 0.0 else 1
            num_of_month = self.env['employee.survey'].search([('response_id', '=', answer.id)]).num_of_month
            tot_in_months += tot_question_result * num_of_month
            total_num_of_month += num_of_month
            self.score_perc = tot_in_months / total_num_of_month if total_num_of_month > 0.0 else 1
            self.total_score = self.score_perc + self.extra_points

    @api.one
    def _compute_performance_level_next_review(self):
        level = self.env['appraisal.levels'].search([], limit=1, order='id DESC')
        if level:
            line = self.env['appraisal.form'].search([('appraisal_id', '=', level.id), ('score_from', '<=', self.total_score), ('score_to', '>=', self.total_score)])
            if len(line) > 1:
                raise exceptions.ValidationError(_("There are two line in appraisal levels has the same score"))
            else:
                self.performance_level = line.performance_level
                if self.performance_level in ('far_exceed', 'exceed', 'accomplish'):
                    self.next_review = self.date_to + relativedelta(months=+line.next_review)

    @api.depends('total_salary')
    def _compute_total_salary(self):
        self.total_salary = self.salary + self.salary_raise


    er_seq = fields.Char(string='ER Number', required=True, copy=False, default='New', track_visibility='always')
    employee_id = fields.Many2one('hr.employee', string='Employee', track_visibility='always')
    date_from = fields.Date(string='Date From', track_visibility='always')
    date_to = fields.Date(string='Date To', track_visibility='always')
    effective_date = fields.Date(string='Effective Date')
    extra_points = fields.Float(string='Extra Points', track_visibility='always')
    score_perc = fields.Float(string='Score Percantage', track_visibility='always', compute='_compute_total_score')
    total_score = fields.Float(string='Total Score', track_visibility='always', compute='_compute_total_score')
    job_id = fields.Many2one('hr.job', string='Current Job Position', track_visibility='always')
    next_job_id = fields.Many2one('hr.job', string='Next Job Position')
    salary = fields.Float(string='Salary', track_visibility='always')
    salary_raise = fields.Float(string='Salary Raise', track_visibility='always')
    total_salary = fields.Float(string='Total Salary', compute="_compute_total_salary")
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

        if self.effective_date == False:
            raise UserError(_("Please, Fill the effective date."))

        today = fields.Date.today()
        if self.effective_date:
            diff_months = today.month - self.effective_date.month

            for i in range(diff_months):
                if i >= diff_months:
                    break
                self.env['hr.expense'].create({
                    'name': "Expense for (%s) Employee" % self.employee_id.name,
                    'employee_id': self.employee_id.id,
                    'unit_amount': self.salary_raise,
                    'product_id': self.env.ref('hr_custom.product_for_expense').id,
                    'Quantity': 1.0,
                })

    @api.onchange('employee_id')
    def _onchange_job_and_salary_appraisal(self):
        if self.employee_id:
            employee = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)])
            self.job_id = employee.job_id
            self.salary = employee.wage


class MonthlySurvey(models.Model):
    _name = 'monthly.survey'

    monthly_id = fields.Many2one('hr.appraisal', string='Monthly')
    description = fields.Text(string='Description')


class EmployeeSurvey(models.Model):
    _name = 'employee.survey'

    appraisal_id = fields.Many2one('hr.appraisal', string='Appraisal')
    employee_id = fields.Many2one('hr.employee', string='Manager')
    response_id = fields.Many2one('survey.user_input', "Response", ondelete="set null", oldname="response")
    survey_id = fields.Many2one('survey.survey', string="Survey")
    status = fields.Selection([('draft', 'Draft'), ('done', 'Done')], string='Status', default='draft')
    num_of_month = fields.Integer(string='No. Of Month')

    @api.onchange('survey_id')
    def _onchange_survey_id(self):
        if self.appraisal_id:
            surveys_ids = self.appraisal_id.job_id.surveys_ids.ids
            return {'domain': {'survey_id': [('id', '=', surveys_ids)]}}

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
        self.status = 'done'
        return self.survey_id.with_context(survey_token=response.token).action_start_survey()


class HRContracts(models.Model):
    _inherit = 'hr.contract'

    department_id = fields.Many2one('hr.department', string="Department", store=True)
    job_id = fields.Many2one('hr.job', string='Job Position', store=True)

    @api.multi
    def create_appraisal(self, vals):
        appraisal_obj = self.env['hr.appraisal']
        start_date = datetime.strptime(vals['date_start'], '%Y-%m-%d')
        appraisal_obj.sudo().create({
            'employee_id': vals['employee_id'],
            'job_id': vals['job_id'],
            'date_from': vals['date_start'],
            'date_to': start_date.date() + relativedelta(years=+1),
            'salary': vals['wage'],
        })

    @api.model
    def create(self, vals):
        if 'employee_id' in vals:
            employee = self.env['hr.employee'].browse(vals['employee_id'])
            vals['job_id'] = employee.job_id.id
            vals['department_id'] = employee.department_id.id
        self.create_appraisal(vals)
        return super(HRContracts, self).create(vals)

    @api.multi
    def add_salary_raise(self):
        contract = self.search([('state', '=', 'open')])
        for rec in contract:
            rec.wage += rec.salary_raise


class HRJob(models.Model):
    _inherit = 'hr.job'

    surveys_ids = fields.Many2many('survey.survey', 'survey_job_rel', 'survey_id', 'job_id', string='Review Survey')


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

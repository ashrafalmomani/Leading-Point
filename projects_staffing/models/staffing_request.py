# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, exceptions


class StaffingRequest(models.Model):
    _name = 'staffing.request'
    _rec_name = 'number'
    _description = 'Staffing Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _default_user_ids(self):
        employee_ids = self.env['hr.employee'].search([('is_staff', '=', True)])
        user_ids = []
        for emp in employee_ids:
            if emp.user_id:
                user_ids.append((4, emp.user_id.id))
        return user_ids

    number = fields.Char('Number', required=True, index=True, copy=False, default='New', track_visibility='always')
    seniority_level = fields.Many2one('seniority.level', string='Seniority Level',  track_visibility='always')
    employee_id = fields.Many2one('hr.employee', 'Employee', track_visibility='always')
    project_id = fields.Many2one('project.project', 'Project', track_visibility='always')
    manager_id = fields.Many2one('hr.employee', 'Project Manager', track_visibility='always')
    current_projects_managers_ids = fields.One2many('current.project', 'project_id', string='Current Projects/Managers')
    category_ids = fields.Many2many('staffing.category', 'category_staffing_rel', 'category_id', 'staffing_id', 'Skils', track_visibility='always')
    start_date = fields.Date('Start Date', track_visibility='always')
    end_date = fields.Date('End Date', track_visibility='always')
    note = fields.Text('Note', track_visibility='always')
    state = fields.Selection([('new', 'New'), ('submit', 'Submitted'), ('confirm', 'Confirmed'), ('cancel', 'Cancel'),
                              ('start', 'Start'), ('finished', 'Finished'), ('stop', 'Stopped')], 'Status', default='new',
                             track_visibility='always')
    user_ids = fields.Many2many('res.users', string='Users', default=_default_user_ids)
    emails = fields.Char('Emails', default='')

    @api.one
    @api.constrains('start_date', 'end_date')
    def check_dates(self):
        if self.end_date < self.start_date:
            raise exceptions.ValidationError(_("End date must be greater than start date!"))

    @api.onchange('user_ids')
    def onchange_user_ids(self):
        if self.user_ids:
            for user in self.user_ids:
                self.emails += user.email + ','

    @api.onchange('project_id')
    def _onchange_project_id(self):
        if self.project_id:
            if self.project_id.user_id.email:
                self.emails += self.project_id.user_id.email + ','
            manager_id = self.env['hr.employee'].search([('user_id', '=', self.project_id.user_id.id)])
            if manager_id:
                self.manager_id = manager_id.id

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            lines = []
            id = self.search([('number', '=', self.number)]).id
            projects = self.env['project.project'].search([('stage_id.close_stage', '!=', True)])
            for proj in projects:
                if self.employee_id.id in proj.staffed_projects_ids.ids:
                    manager_id = self.env['hr.employee'].search([('user_id', '=', proj.user_id.id)])
                    lines.append([0, False, {'project_id': id, 'projects_id': proj.id, 'manager_id': manager_id.id or False}])
            self.current_projects_managers_ids = lines

    @api.model
    def create(self, vals):
        number = self.env['ir.sequence'].next_by_code('staffing.request') or '/'
        vals.update({'number': number})
        return super(StaffingRequest, self).create(vals)

    @api.multi
    def submit_action(self):
        self.write({'state': 'submit'})

    @api.multi  # TODO get the followers of the active Scrum Project
    def get_partner_ids(self, user_ids):
        return str([user_ids.ids]).replace('[', '').replace(']', '')

    @api.multi
    def confirm_action(self):
        if self.project_id:
            self.project_id.write({'staffed_projects_ids': [(4, self.employee_id.id)]})
            self.project_id.write({'members': [(4, self.employee_id.id)]})
        self.write({'state': 'confirm'})

        template_id = self.env.ref('projects_staffing.email_template_project_managers').id
        composer = self.env['mail.compose.message'].sudo().with_context({
            'default_composition_mode': 'mass_mail',
            'default_notify': False,
            'default_model': 'project.project',
            'default_res_id': self.id,
            'default_template_id': template_id,
        }).create({})
        values = composer.onchange_template_id(template_id, 'mass_mail', 'project.project', self.id)['value']
        composer.write(values)
        composer.send_mail()

    @api.multi
    def cancel_action(self):
        if self.project_id:
            self.project_id.write({'staffed_projects_ids': [(3, self.employee_id.id)]})
            self.project_id.write({'members': [(3, self.employee_id.id)]})
        self.write({'state': 'cancel'})

    @api.multi
    def stopped_action(self):
        if self.project_id:
            self.project_id.write({'members': [(3, self.employee_id.id)]})
        self.write({'state': 'cancel'})

    @api.multi
    def _check_staffing_status(self):
        staff_ids = self.search([('state', '=', 'confirm')])
        for rec in staff_ids:
            current_day = fields.Date.today()
            start_date = rec.start_date
            end_date = rec.end_date
            if start_date == current_day:
                rec.state = 'start'
            elif end_date == current_day:
                rec.state = 'finished'
                rec.project_id.write({'staffed_projects_ids': [(3, self.employee_id.id)]})


class StaffingCategory(models.Model):
    _name = 'staffing.category'
    _rec_name = 'name'
    _description = 'Staffing Category'

    name = fields.Char('Name', required=True)


class ProjectProject(models.Model):
    _inherit = 'project.project'

    staffed_projects_ids = fields.Many2many('hr.employee', 'project_staff_rel', 'project_id', 'staff_id', string='Staff')

    @api.multi
    def projects_staffing(self):
        return {
            'name': _('Staff'),
            'domain': [('project_id', 'in', [self.id])],
            'res_model': 'staffing.request',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'target': 'current'}


class SeniorityLevels(models.Model):
    _name = 'seniority.level'
    _description = 'Staffing Seniority Level'

    name = fields.Char(string='Name')


class EmployeeDirector(models.Model):
    _inherit = 'hr.employee'

    is_staff = fields.Boolean(string='Is Staff Director')


class CurrentProjects(models.Model):
    _name = 'current.project'

    project_id = fields.Many2one('staffing.request', string='Project')
    projects_id = fields.Many2one('project.project', string='Projects')
    manager_id = fields.Many2one('res.users', string='Managers')

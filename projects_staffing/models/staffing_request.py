# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class StaffingRequest(models.Model):
    _name = 'staffing.request'
    _rec_name = 'number'
    _description = 'Staffing Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    number = fields.Char('Number', required=True, index=True, copy=False, default='New', track_visibility='always')
    seniority_level = fields.Selection([('trainee', 'Trainee'), ('senior', 'Senior'), ('manager', 'Manager'), ('director', 'Director')], 'Seniority Level',  track_visibility='always')
    employee_id = fields.Many2one('hr.employee', 'Employee', track_visibility='always')
    project_id = fields.Many2one('project.project', 'Project', track_visibility='always')
    manager_id = fields.Many2one('hr.employee', 'Project Manager', track_visibility='always')
    current_projects_ids = fields.Many2many('project.project', 'project_staffing_rel', 'project_id', 'staffing_id', 'Current Projects', track_visibility='always')
    current_projects_managers_ids = fields.Many2many('hr.employee', 'project_manager_staffing_rel', 'employee_id', 'staffing_id', 'Current Managers', track_visibility='always')
    category_ids = fields.Many2many('staffing.category', 'category_staffing_rel', 'category_id', 'staffing_id', 'Category', track_visibility='always')
    start_date = fields.Date('Start Date', track_visibility='always')
    end_date = fields.Date('End Date', track_visibility='always')
    note = fields.Text('Note', track_visibility='always')
    state = fields.Selection([('new', 'New'), ('submit', 'Submitted'), ('confirm', 'Confirmed'), ('cancel', 'Cancel'),
                              ('start', 'Start'), ('finsh', 'Finished')], 'Status', default='new',
                             track_visibility='always')

    @api.onchange('project_id')
    def _onchange_project_id(self):
        if self.project_id:
            manager_id = self.env['hr.employee'].search([('user_id', '=', self.project_id.user_id.id)])
            if manager_id:
                self.manager_id = manager_id.id

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            employee_projects = []
            employee_managers = []
            projects = self.env['project.project'].search([('stage_id.close_stage', '!=', True)])
            for proj in projects:
                if self.employee_id.id in proj.members.ids:
                    employee_projects.append(proj.id)
                    manager_id = self.env['hr.employee'].search([('user_id', '=', proj.user_id.id)])
                    if manager_id:
                        employee_managers.append(manager_id.id)
            self.current_projects_ids = [(6, 0, employee_projects)]
            self.current_projects_managers_ids = [(6, 0, employee_managers)]
            return {'domain': {'current_projects_ids': [('id', 'in', employee_projects)],
                               'current_projects_managers_ids': [('id', 'in', employee_managers)]}}
        else:
            return {'domain': {'current_projects_ids': [('id', '=', [])],
                               'current_projects_managers_ids': [('id', '=', [])]}}

    @api.model
    def create(self, vals):
        number = self.env['ir.sequence'].next_by_code('staffing.request') or '/'
        vals.update({'number': number})
        return super(StaffingRequest, self).create(vals)

    @api.multi
    def submit_action(self):
        self.write({'state': 'submit'})

    @api.multi
    def confirm_action(self):
        if self.project_id:
            # self.project_id.write({'staffed_projects': [(4, self.project_id.id)]})
            self.project_id.write({'members': [(4, self.project_id.id)]})
        self.write({'state': 'confirm'})

    @api.multi
    def cancel_action(self):
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
                rec.state = 'finsh'
                # rec.project_id.write({'staffed_projects': [(3, self.project_id.id)]})


class StaffingCategory(models.Model):
    _name = 'staffing.category'
    _rec_name = 'name'
    _description = 'Staffing Category'

    name = fields.Char('Name', required=True)


class ProjectProject(models.Model):
    _inherit = 'project.project'

    # staffed_projects = fields.Many2many('project.project', string='Project')

    @api.multi
    def projects_staffing(self):
        return {
            'name': _('Staffing Request'),
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': 'active_id'},
            'res_model': 'staffing.request',
            'type': 'ir.actions.act_window',
            'views': [(self.env.ref('staffing_request_tree').id, 'tree')],
            'view_type': 'tree',
            'view_mode': 'tree,',
            'target': 'current'}

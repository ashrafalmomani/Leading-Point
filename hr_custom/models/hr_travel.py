# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HREmployeeTravel(models.Model):
    _name = "hr.travel"
    _description = 'Travel'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'number'

    number = fields.Char('Number', required=True, copy=False, default='New')
    employee = fields.Many2one('hr.employee', string='Employee')
    project = fields.Many2many('project.project', string='Project')
    lead = fields.Many2many('crm.lead', string='Lead/Opportunity')
    origin = fields.Many2one('res.country.state', string='Origin')
    destination = fields.Many2one('res.country.state', string='Destination')
    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    visa_required = fields.Boolean(string='Visa')
    hotel_required = fields.Boolean(string='Hotel')
    other_info = fields.Text(string='Other Information')
    travel_ids = fields.One2many('hr.tickets', 'tickets_id', string='Tickets')
    hotel_ids = fields.One2many('hr.hotels', 'hotel_id', string='Hotels')
    visa_ids = fields.One2many('hr.visas', 'visa_id', string='Visas')
    manager_id = fields.Many2one('hr.employee', string='Manager')
    reason_for_travel = fields.Selection([('project', 'Project'),
                                          ('business_dev', 'Business Development'),
                                          ('visa_renewal', 'Visa Renewal'),
                                          ('other', 'Other')], string='Reason For Travel')

    state = fields.Selection([('draft', 'Draft'),
                              ('submitted', 'Submitted'),
                              ('manager_approved', 'Manager Approved'),
                              ('company_approved', 'Company Approved'),
                              ('rejected', 'Rejected')], default='draft', store=True)

    trip_status = fields.Selection([('not_started', 'Not Started'),
                                    ('preparing', 'Preparing'),
                                    ('ready', 'Ready'),
                                    ('open', 'Open'),
                                    ('closed', 'Closed')], string='Trip Status', default='not_started')

    @api.model
    def create(self, vals):
        number = self.env['ir.sequence'].next_by_code('hr.travel') or '/'
        vals.update({'number': number})
        return super(HREmployeeTravel, self).create(vals)

    @api.multi
    def action_submit(self):
        self.state = 'submitted'

    @api.multi
    def action_approve_by_manager(self):
        self.state = 'manager_approved'

    @api.multi
    def action_approve_by_company(self):
        self.state = 'company_approved'

    @api.multi
    def action_reject(self):
        self.state = 'rejected'

    @api.multi
    def action_set_to_draft(self):
        self.state = 'draft'

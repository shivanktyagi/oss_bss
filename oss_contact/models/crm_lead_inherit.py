# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2022 (https://www.in2ittech.com)
#
##############################################################################

import logging


from odoo import models, api, fields, _, exceptions, tools, SUPERUSER_ID

_logger = logging.getLogger(__name__)

class UtmSource(models.Model):
    _inherit = 'utm.source'

    active = fields.Boolean(default=True, help="Set active to false to hide the Source without removing it.")

class LostReason(models.Model):
    _inherit = "crm.lost.reason"

    stage_ids = fields.Many2one('crm.stage', 'Stage')

class CrmStage(models.Model):
    _inherit = "crm.stage"

    is_lead = fields.Selection([('lead','Lead'),('opportunity','Opportunity')])
    default_stage = fields.Boolean('Default Stage')
    feasibility_stage = fields.Boolean('Feasibility Stage')

class SaleOrder(models.Model):
    _inherit = "sale.order"

    progress_bar = fields.Selection([('propose', 'Propose'),('deliver', 'Deliver')], string='Progress Bar', compute="compute_progress_bar", store=True)
    case_id = fields.Char(related="opportunity_id.case_id", string='Case ID', copy=False, tracking=True)

    @api.depends('state')
    def compute_progress_bar(self):
        for so in self:
            so.progress_bar = 'deliver' if so.state == 'sale' else 'propose'

class Lead(models.Model):
    _inherit = "crm.lead"

    #main Page fields
    product_ids = fields.Many2many('product.template', string='Enquiry Products', required=True, tracking=True)
    case_id = fields.Char('Case ID', copy=False, tracking=True)
    task_ids = fields.One2many('crm.lead.tasks', 'lead_id', string="Tasks")
    stakeholder_ids = fields.One2many('crm.lead.stakeholders', 'lead_id', string="Stakeholders")
    task_count = fields.Integer(compute='_compute_task_data', string="Number of Task", tracking=True)
    stakeholder_count = fields.Integer(compute='_compute_task_data', string="Number of stakeholder", tracking=True)
    # product_package = fields.Many2one('product.package')
    purchase_process = fields.Selection([
        ('purchase', 'Purchase Order'),
        ('good_receipt', 'Goods receipt'),
        ('invoice_receipt', 'Invoice receipt'),
        ('vendor_payment', 'Vendor Payment'),
    ], string="Purchase Process", tracking=True)
    linked_lead_ids = fields.One2many("crm.lead", "parent_id", string="Linked Leads")
    parent_id = fields.Many2one("crm.lead", string="Parent Leads")
    linked_lead_count = fields.Integer(compute="_compute_linked_leads", string="Linked Leads Count", tracking=True)

    # main page core fields enable tracking *
    name = fields.Char(tracking=True)
    street = fields.Char(tracking=True)
    street2 = fields.Char(tracking=True)
    city = fields.Char(tracking=True)
    state_id = fields.Many2one(tracking=True)
    zip = fields.Char(tracking=True)
    country_id = fields.Many2one(tracking=True)
    date_deadline = fields.Date(tracking=True)
    priority = fields.Selection(tracking=True)
    tag_ids = fields.Many2many(tracking=True)
    source_id = fields.Many2one(tracking=True)
    team_id = fields.Many2one(tracking=True)

    stage_id = fields.Many2one('crm.stage', group_expand='_read_group_stage_ids', string='Stage', tracking=True,
    domain="[('is_lead', '=', type)]", readonly=False, ondelete='restrict')

    # Summary Details Fields
    security_requirement_ids = fields.Many2many('security.requirement', string='Security Requirements', required=True, tracking=True)
    business_req_product = fields.Char('Business Requirement for product', tracking=True)
    product_value_business = fields.Selection([
        ('critical', 'Critical'),
        ('very_high', 'Very High'),
    ], string="Product value Business", tracking=True)
    # final_products = fields.Many2many('product.template', string='Final Products')
    expected_delivery_date = fields.Date('Expected Delivery Date', tracking=True)
    to_delivery_date = fields.Date('To', tracking=True)
    remarks = fields.Text("Remarks", tracking=True)
    is_spoc = fields.Boolean('Add another SPOC', tracking=True)
    spoc_name = fields.Char('SPOC Name', tracking=True)
    spoc_email = fields.Char('Site SPOC Email', tracking=True)
    spoc_contact_number = fields.Char('SPOC Contact Number', tracking=True)

    # General Details Fields
    no_of_sites = fields.Integer(string='Number of Sites', compute="_compute_no_of_site", tracking=True)
    topology_requirement = fields.Selection([
        ('hub_spoke', 'Hub & Spoke '),
        ('full_mesh', 'Full Mesh'),
        ('partial_mesh', 'Partial Mesh')
    ], string="Topology Requirement", tracking=True)

    is_public_cloud_access = fields.Boolean('Public Cloud Access', tracking=True)
    public_cloud_name = fields.Selection([
        ('azure', 'Azure'),
        ('GCP', 'GCP'),
        ('AWS', 'AWS')
    ], string="Public Cloud Name", tracking=True)
    public_bandwidth = fields.Char('Public Bandwidth', tracking=True)
    existing_routing_protocol = fields.Selection([
        ('ospf', 'OSPF'),
        ('bgp', 'BGP'),
        ('static', 'STATIC')
    ], string='Existing Routing Protocol', tracking=True)
    cpe_requirement = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='CPE Requirement', tracking=True)
    cpe_model_ids = fields.One2many('cpe.product', 'product_cpe_id', string="CPE Model's", copy=True, auto_join=True)
    site_internet_usage = fields.Selection([
        ('centralize', 'Centralize'),
        ('dia', 'DIA')
    ], string='Site Internet Usage', tracking=True)

    url_filtering = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='URL Filtering', tracking=True)
    intrusion_prevention_system = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Intrusion Prevention System', tracking=True)
    local_attack_defence = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Local Attack Defense', tracking=True)
    malware_protection = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Malware Protection', tracking=True)

    # Sites Details Fields
    site_address_ids = fields.One2many('res.partner', 'partner_site_id', string='Sites', tracking=True)
   
    # Cloud On Ramp Details Fields
    enable_cloud_on_ramp = fields.Boolean(string="Enable Cloud On Ramp")
    cor_ramp_ids = fields.One2many('cloud.ramp', 'lead_id', string="CoR on Ramp", tracking=True)
    no_of_cor_sites = fields.Integer(string="No. of CoR Sites", compute="_compute_cor_sites")

    # Application Details Fields
    is_application_modelling = fields.Boolean(string="Enable App Modelling")
    app_modeling_ids = fields.One2many('app.modeling', 'lead_id', string="App Modeling for Sites", tracking=True)
    no_of_applications = fields.Integer(string="No. of Applications", compute="_compute_applications")

    # Lost Additional Remark
    lost_additional_remark = fields.Char(string='LR Additonal Remarks', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency', tracking=True)
    estimated_budget = fields.Monetary(string="Estimated Budget", currency_field='currency_id', tracking=True)
    progress_bar = fields.Selection([('qualify', 'Qualify'),('develop', 'Develop')], string='Progress Bar', compute="compute_progress_bar", store=True, tracking=True)
    contract_duration = fields.Selection([('one', '1 Year'),('two', '2 Years'),('three', '3 Years'),('four', '4 Years')], string='Contract Duration', tracking=True)
    billing_cycle = fields.Selection([
        ('monthly', 'Monthly'),('bi_monthly','Bi-Monthly'),
        ('quarterly','Quarterly'),('half_yearly','Half Yearly'),
        ('yearly', 'Yearly'),
        ], string='Billing Cycle', tracking=True)

    #Opportunity Field *
    offered_discount = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Offered Discount', tracking=True)
    payment_mode = fields.Selection([
        ('online', 'UPI/NetBanking/Card '),
        ('cheque', 'Cheque'),
        ('cash', 'Cash')
    ], string='Payment Mode', tracking=True)
    certainity = fields.Many2one('crm.certainity', string='Certainity', tracking=True)
    estimate_revenue = fields.Monetary(string="Estimated Revenue", currency_field='currency_id', tracking=True)
    total_rc = fields.Monetary(string="Total YRC", currency_field='currency_id', tracking=True)
    total_nrc = fields.Monetary(string="Total NRC", currency_field='currency_id', tracking=True)
    total_mrc = fields.Monetary(string="Total MRC", currency_field='currency_id', tracking=True)
    contract_penalty = fields.Monetary(string="Contract Penalty", currency_field='currency_id', tracking=True)
    closure_date = fields.Date(string="Closure Date", tracking=True)

    feasibility_stage = fields.Boolean(related='stage_id.feasibility_stage')
    active = fields.Boolean('Active', default=True, tracking=False)

    @api.model
    def default_get(self, fields):
        res = super(Lead, self).default_get(fields)
        res['stage_id'] = self.env['crm.stage'].sudo().search([('is_lead','=',res.get('type')),('default_stage','=',True)],limit=1).id
        return res

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        type = self._context.get('default_type')
        search_domain = [('id', 'in', stages.ids),('is_lead','=',type)]
        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    @api.depends('type')
    def compute_progress_bar(self):
        for lead in self:
            lead.progress_bar = 'qualify' if lead.type == 'lead' else 'develop'

    @api.model
    def create(self, values):
        if 'case_id' not in values:
            case_id = self.env['ir.sequence'].next_by_code(
                'enquiry_sequence') or _('New')
            product_name = self.env['product.template'].sudo().browse(values.get('product_ids')[0][2]).name
            values['case_id'] = product_name[0:3] + case_id
        return super(Lead, self).create(values)
    
    @api.depends('cor_ramp_ids')
    def _compute_cor_sites(self):
        for lead in self:
            lead.no_of_cor_sites = len(lead.cor_ramp_ids)

    @api.depends('app_modeling_ids')
    def _compute_applications(self):
        for lead in self:
            lead.no_of_applications = len(lead.app_modeling_ids)

    @api.depends('task_ids', 'stakeholder_ids')
    def _compute_task_data(self):
        for lead in self:
            lead.task_count = len(lead.task_ids)
            lead.stakeholder_count = len(lead.stakeholder_ids)

    def dynamic_button(self):
        pass

    def _compute_no_of_site(self):
        for obj in self:
            obj.no_of_sites = len(self.site_address_ids.ids)

    def _compute_linked_leads(self):
        for obj in self:
            obj.linked_lead_count = len(obj.linked_lead_ids.ids)

    def action_show_linked_leads(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_opportunities")
        action['domain'] = [('id', 'in', self.linked_lead_ids.ids)]
        action['context'] = {
            'create': False
        }
        return action

    def action_new_quotation(self):
        action = super(Lead, self).action_new_quotation()
        if self.product_ids:
            prod = self.env['product.product'].search([('product_tmpl_id','=',self.product_ids[0].id)], limit=1)
            action['context']['default_order_line'] = (0, 0, {
                'name': prod.name,
                'product_id': prod.id,
                'product_uom_qty': 1,
                'product_uom': self.product_ids[0].uom_po_id.id,
                'price_unit': self.estimated_budget,
            }),
        return action

    # def redirect_lead_opportunity_view(self):
    #     self.ensure_one()
    #     develop_stage_id = self.env['crm.stage'].search([('default_stage','=',True),('is_lead','=','opportunity')])
    #     return {
    #         'name': _('Lead or Opportunity'),
    #         'view_mode': 'form',
    #         'res_model': 'crm.lead',
    #         'domain': [('type', '=', self.type)],
    #         'res_id': self.id,
    #         'view_id': False,
    #         'type': 'ir.actions.act_window',
    #         'context': {'default_type': self.type, 'default_stage_id':develop_stage_id.id}
    #     }

class CPEProduct(models.Model):
    _name = 'cpe.product'
    _description = "CPE Model's"

    product_cpe_id = fields.Many2one(
        'crm.lead', string="CPE's", ondelete='cascade', index=True, copy=False)
    oem_model_id = fields.Many2one("product.brands", string="OEM Model")
    product_id = fields.Many2one(
        'product.product', string='CPE Model', domain="[('sale_ok', '=', True),('oem_model_id', '=', oem_model_id)]",
        change_default=True, ondelete='restrict')  # Unrequired company
    product_template_id = fields.Many2one(
        'product.template', string='Product Template',
        related="product_id.product_tmpl_id", domain=[('sale_ok', '=', True)])

    no_of_devices = fields.Float(string='No. of Devices', required=True, default=1.0)

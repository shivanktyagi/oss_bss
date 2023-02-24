# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2022 (https://www.in2ittech.com)
#
##############################################################################

import logging
from odoo import models, api, _, fields, exceptions
from odoo.exceptions import UserError


AVAILABLE_PRIORITIES = [
    ('0', 'Low'),
    ('1', 'P1'),
    ('2', 'P2'),
    ('3', 'P3'),
    ('4', 'P4'),
]

_logger = logging.getLogger(__name__)

class CustomerLead(models.Model):
    _name = "customer.lead"

    _description = "Customer Lead/Opportunity"
    _rec_name = "partner_id"
    _order = "id desc"


    company_name = fields.Char('Company Name')
    title = fields.Many2one('res.partner.title', string='Title', compute='_compute_title', readonly=False, store=True)
    first_name = fields.Char('First Name')
    middle_name = fields.Char('Middle Name')
    last_name = fields.Char('Last Name')
    designation = fields.Char('Designation')
    phone = fields.Char('Phone', tracking=50,store=True)
    mobile = fields.Char('Mobile', store=True)
    email = fields.Char('Email', store=True)
    # partner = fields.Selection([('new','New'),('existing','Existing')], string='Customer')
    partner_id = fields.Many2one('res.partner', string="Company Name")


    state = fields.Selection([
        ('new', 'Opportunity'),
        ('sent', 'Quotation Sent'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='new')

    # Requirement Details
    no_of_sites = fields.Integer('No. of Sites')
    topology = fields.Selection([('hub_spoke','Hub & Spoke'),('fuull_mesh','Full Mesh'),('partial_mesh','Partial Mesh')], string='Topology')
    minimum_service_period = fields.Char('Minimum Service Period (Months)')
    cloud_on_ramp = fields.Selection([('yes','Yes'),('no', 'NO')],string='Cloud On-Ramp')
    leble_cloud = fields.Char('Huawei SD-WAN Solution, the AR1000V, a virtual router')
    billing_cycle = fields.Selection([('quarterly','Quarterly'),('bi-annual','Bi-Annual'),('annually','Annually')],string='Billing Cycle')
    routing_protocol = fields.Selection([('ospf','OSPF'),('bgp','BGP'),('static','Static')], string='Existing Routing Protocol')
    cpe = fields.Selection([('new','New'),('existing','Existing')], string='CPE Requirement')
    product_id = fields.Many2one('product.product',string='Devices Name')
    no_of_applications = fields.Char('No. of Applications')
    no_of_device = fields.Integer('No of Devices', compute='_compute_use_devices')

    site_address_ids = fields.One2many('res.partner', 'customer_id', string='Sites')
    applications_ids = fields.One2many('customer.application', 'application_id', string='Applications')
    internet_policy_ids = fields.One2many('internet.policies', 'internet_policy_id', string='Internet Policies')

    # Internet Usage and Security Policy
    branch_site_internet_usage_id = fields.Many2many('branch.site', string='Branch Site Internet Usage')
    url_filtering = fields.Selection([('yes','Yes'),('no','No')], string='URL Filtering')
    intrusion_prevention_system = fields.Selection([('yes','Yes'),('no','No')], string='Intrusion Prevention System')
    local_attack_defence = fields.Selection([('yes','Yes'),('no','No')], string='Local Attack Defence')
    malware_protection = fields.Selection([('yes','Yes'),('no','No')], string='Malware Protection')
    sale_order_id = fields.Many2one('sale.order',string="Quotation Id") 

    def _compute_use_devices(self):
        for record in self:
            total_device = 0
            for site_id in record.site_address_ids:
                if site_id.redundancy_requirement.name == 'Device Level':
                    total_device  = total_device +2
                if site_id.redundancy_requirement.name == 'Link Level':
                    total_device  = total_device + 1
            record.no_of_device = total_device



    def convert_quotation(self):
        sale_order_obj = self.env['sale.order'].sudo()
        # Product Check 
        if self.product_id:
            order_line_dict = {}

            vals = ({
                    'partner_id': self.partner_id.id,
                    'state' : 'draft',
                    'order_line': [[0, 0, {
                        'name':  self.product_id.name,
                        'product_id': self.product_id.id,
                        'product_uom_qty': self.no_of_device,
                        'price_unit': self.product_id.list_price,
                    }]]
            })
            order_id = sale_order_obj.create(vals)
            self.state = 'sent'
            self.sale_order_id = order_id.id
        else:
            raise UserError(_("Can't find Product base on customer requirement.Please contact to sale person."))
 

class BranchSite(models.Model):
    _name = "branch.site"
    _description = 'Branch Site'

    name = fields.Char('branch Site Name')


class Application(models.Model):
    _name = "customer.application"
    _description = "Customer Application"
    _rec_name = "application_name"

    application_name = fields.Char('Application Name')
    color = fields.Integer(string='Color Index', default=0)

    application_hosted = fields.Selection([('on_premises','On-Premises'),('public','Public Cloud'),('msp','MSP')], string='Application Hosted')
    concurrent_users = fields.Integer('Concurrent Users')
    bandwidh = fields.Integer('Bandwidth(Per/session)')
    qos_parameter = fields.Selection([('delay','Delay'),('jitter','Jitter'),('packet_drop','Packet Drop')], string='QoS Parameter')
    priority = fields.Selection(AVAILABLE_PRIORITIES, string='Priority for Business', index=True,
        default=AVAILABLE_PRIORITIES[0][0])

    application_id = fields.Many2one('customer.lead', string='Application')


class InternetPolicy(models.Model):
    _name = "internet.policies"
    _description = "Internet Policies"

    # Internet Usage and Security Policy
    internet_policy_id = fields.Many2one('customer.lead', string='Internet Policies')
    site_id = fields.Many2one('res.partner', string="Site Name")
    branch_site_internet_usage_id = fields.Many2many('branch.site', string='Branch Site Internet Usage')
    url_filtering = fields.Selection([('yes','Yes'),('no','No')], string='URL Filtering')
    intrusion_prevention_system = fields.Selection([('yes','Yes'),('no','No')], string='Intrusion Prevention System')
    local_attack_defence = fields.Selection([('yes','Yes'),('no','No')], string='Local Attack Defence')
    malware_protection = fields.Selection([('yes','Yes'),('no','No')], string='Malware Protection')

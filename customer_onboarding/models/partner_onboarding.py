# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2022 (https://www.in2ittech.com)
#
##############################################################################

import logging
from odoo import models, api, fields, exceptions

_logger = logging.getLogger(__name__)

class Partner(models.Model):
    _inherit = "res.partner"

    type = fields.Selection(
        [('contact', 'Contact Details'),
         ('invoice', 'Invoice Address'),
         ('delivery', 'Delivery Address'),
         ('branch', 'Branch Details'),
         ('other', 'Other Address'),
        ], string='Address Type',
        default='contact',
        help="Invoice & Delivery addresses are used in sales orders. Private addresses are only visible by authorized users.")
    company_type = fields.Selection(string='Company Type',
        selection=[('person', 'Person'), ('company', 'Company')],
        compute='_compute_company_type', inverse='_write_company_type')

    office_type = fields.Selection(
        [('head_office', 'Head Office'),
         ('disaster_recovery', 'Disaster Recovery'),
         ('branch', 'Branch Details'),
        ], string='Office Type',
        default='branch')

    designation = fields.Char('Designation')
    site_name = fields.Char('Office Site Name')
    office_address = fields.Text('Office Address')
    first_name = fields.Char('First Name')
    middle_name = fields.Char('Middle Name')
    last_name = fields.Char('Last Name')
    extension = fields.Char('Extension Number')
    site_type  = fields.Selection([('Normal','Normal'),('Cloud','Cloud')], string= 'Site Type')
    redundancy_requirement = fields.Many2one('redundancy.requirement', string='Redundancy Requirement')
    
    # Existing Transport Link 
    existing_transport_link  = fields.Selection([('yes','Yes'),('no','No')], string='Existing Transport Link')
    transport_link_1_type = fields.Selection([
        ('MPLS','MPLS'),('Internet','Internet'),('LTE','LTE')], string= 'Link-1 Type')
    transport_link_1_bandwidth =  fields.Char('Link-1 Bandwidth (Kbps)') 
    transport_link_1_sla = fields.Char('Link-1 SLA')
    transport_link_1_media = fields.Char('Link-1 Media')

    transport_link_2_type = fields.Selection([
        ('MPLS','MPLS'),('Internet','Internet'),('LTE','LTE')], string= 'Link-2 Type')
    transport_link_2_bandwidth =  fields.Char('Link-2 Bandwidth (Kbps)') 
    transport_link_2_sla = fields.Char('Link-2 SLA')
    transport_link_2_media = fields.Char('Link-2 Media')

    router_1_model = fields.Many2one('hardware.router', string='Router-1 Model')
    router_2_model = fields.Many2one('hardware.router', string='Router-2 Model')
    support_level = fields.Char('Support Level')
    office_site_sla = fields.Char('Office Site SLA')
    customer_id = fields.Many2one('customer.lead', string="Customer")



class RedundancyRequirement(models.Model):
    _name = "redundancy.requirement"
    _description = 'Redundancy Requirement'

    name = fields.Char('Redundancy Name')

class Router(models.Model):
    _name = "hardware.router"
    _description = 'Hardware Router'

    name = fields.Char('Router Name')




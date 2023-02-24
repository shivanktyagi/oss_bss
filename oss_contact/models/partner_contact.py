# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2022 (https://www.in2ittech.com)
#
##############################################################################

import logging
from odoo import models, api, fields, exceptions, _
from odoo.exceptions import UserError, ValidationError


_logger = logging.getLogger(__name__)

class Partner(models.Model):
    _inherit = "res.partner"

    #  Contact Fields
    is_contact = fields.Boolean('Is Conatact')
    designation = fields.Char('Designation')
    organization = fields.Char('Organization Name')

    organization_registration = fields.Char('Organization Registration')
    department = fields.Char('Department')

    preferred_language = fields.Many2one('res.lang', 'Preferred Language')
    product_preferences = fields.Many2one('product.product', 'Product Preferences')
    industry_other = fields.Char('Industry type')
    remark = fields.Text('Remarks')
    gov_id = fields.Selection(
        [('driving_licence', 'Driving Licence'),
            ('passport', 'Passport'),
            ('naional_id', 'National ID Card')
        ], string="Govt ID")
    gov_number = fields.Char('Govt ID Number')
    state = fields.Selection(
            [('contact', 'Contact'),('customer', 'Customer')])


    # Site Information fields
    name = fields.Char(tracking=True, required=True)
    site_code = fields.Char('Site Code', tracking=True)
    partner_site_id = fields.Many2one('crm.lead', string="Lead", tracking=True)
    is_site = fields.Boolean('Is site', tracking=True)
    site_type = fields.Selection([
        ('head_office', 'Head Office'),
        ('disaster_recovery', 'Disaster Recovery'),
        ('branch', 'Branch'),
    ], string='Office Type', default='branch', tracking=True)
    hosting_models = fields.Selection([
        ('on_premise', 'On Premise'),
        ('public_cloud', 'Public Cloud'),
        ('msp', 'MSP'),
    ], string='Hosting Model', tracking=True)

    name_of_site = fields.Char(string='Name of Site', tracking=True)
    spoc_name = fields.Char('First Name', tracking=True)
    spoc_lname = fields.Char('Last Name', tracking=True)
    site_sla = fields.Char('Site SLA', tracking=True)
    last_mile_connectivity = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Do You have SITA Last Mile Connectivity?', tracking=True)

    existing_id = fields.Char(string='Existing ID for Transport Link', tracking=True)
    existing_site_code = fields.Char(string='Existing Site Code', tracking=True)

    redundancy_requirement = fields.Selection([
        ("device_level", "Device Level with dual Link"),
        ("link_level", "Link Level"),
        ("none", "None"),
    ], string="Redundancy Requirement", tracking=True)
    hardware_support_level = fields.Char(string='Hardware Support Level', tracking=True)
    head_office_site_sla = fields.Char(string='Head Office Site SLA', tracking=True)

    tp_link_model_id = fields.One2many('transport.links', 'transport_link_id', string='Transport Links', tracking=True)
    router_ids = fields.Many2many('product.product', string='Routers', tracking=True)

    wireless_for_lan = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Wireless for LAN', tracking=True)
    site_internet_usage = fields.Selection([
        ('centralize', 'Centralize'),
        ('dia', 'DIA')
    ], string='Internet Usage', tracking=True)
    # Organisation Contact
    organisation_id = fields.Many2one('res.partner', required=True, domain=[('is_organisation', '=', True)])
    spoc_role = fields.Selection([('1', 'Org SPOC'),('2', 'Bank SPOC'),('3', 'Site SPOC'),('4','Other')], string='Role')
    is_org_contact = fields.Boolean()
    other_role = fields.Char(string='Other Role')
    other_detail_ids = fields.One2many('contact.other.detail', 'org_contact_id', string='Other Details')
    org_contact_ids = fields.Many2many('res.partner', 'org_contact', 'org_id', 'contact_id', string='Contacts', compute='_compute_org_contact', tracking=True)
    preferred_type = fields.Char(string='Preferred Type')
    email_enable = fields.Boolean(string="Email Enable")
    phone_enable = fields.Boolean(string="Phone Enable")
    phone_code = fields.Char(string='Phone Code')
    # Organisation
    is_organisation = fields.Boolean()
    registration_no = fields.Char(string='Registration No.', required=True,)
    parent_organisation_id = fields.Many2one('res.partner', string='Parent Organisation', index=True)
    spoc_id = fields.Many2one('res.partner', string='SPOC', domain=[('is_org_contact', '=', True), ('spoc_role', '=', "org_spoc"), ('organisation_id', '=', False)])
    same_as_org_address = fields.Boolean()
    invoice_address_1 = fields.Char(required=True)
    invoice_address_2 = fields.Char(required=True)
    invoice_zip = fields.Char(required=True)
    invoice_city = fields.Char(required=True)
    invoice_state_id = fields.Many2one('res.country.state', required=True)
    invoice_country_id = fields.Many2one('res.country', string="Country", required=True)
    no_of_account = fields.Integer(compute='_compute_no_of_account')

    # @api.onchange('spoc_id')
    # def _onchange_spoc_id(self):
    #     context = dict(self._context.get('params'))
    #     active_id = context.get('id')
    #     if self.spoc_id:
    #         self.spoc_id.organisation_id = active_id
    #         self.spoc_id.is_org_contact = True
    #         # self.spoc_id.is_org_spoc = True

    def get_sites_records(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("oss_contact.action_sites")
        action['domain'] = [('organisation_id', 'in', self.ids)]
        action['context'] = {
            'create': False
        }
        return action

    @api.depends('organisation_id')
    def _compute_org_contact(self):
        for rec in self:
            cnt_ids = self.search([('is_org_contact', '=', True), ('organisation_id', '=', rec.id)])
            rec.org_contact_ids = [(6, 0, cnt_ids.ids)] if cnt_ids else False

    def _compute_no_of_account(self):
        for obj in self:
            obj.no_of_account = len(self.bank_ids.ids)

    @api.onchange('same_as_org_address')
    def onchange_billing_address(self):
        self.invoice_address_1 = False
        self.invoice_address_2 = False
        self.invoice_zip = False
        self.invoice_city = False
        self.invoice_country_id = False
        self.invoice_state_id = False
        if self.same_as_org_address:
            self.update({
                'invoice_address_1': self.street,
                'invoice_address_2': self.street2,
                'invoice_zip': self.zip,
                'invoice_city': self.city,
                'invoice_state_id': self.state_id.id,
                'invoice_country_id': self.country_id.id
            })


    @api.model
    def create(self, values):
        if 'site_code' not in values:
            crm_id = self.env['crm.lead'].sudo().browse(values.get('partner_site_id'))
            if crm_id.partner_id:
                s_id = self.env['ir.sequence'].next_by_code(
                    'site_sequence') or _('New')
                c_name = crm_id.partner_id.name[:3]
                s_type = values.get('site_type')
                h_model = values.get('hosting_models')
                e_product = crm_id.product_ids.name[:3] if crm_id.product_ids else ''
                if h_model == 'public_cloud':
                    values['site_code'] = (c_name + s_id + 'C' + s_type[0] + e_product).upper()
                if h_model == 'on_premise':
                    values['site_code'] = (c_name + s_id + 'P' + s_type[0] + e_product).upper()
                else:
                    values['site_code'] = (c_name + s_id + h_model[0] + s_type[0] + e_product).upper()
        return super(Partner, self).create(values)

    def convert_customer(self):
        self.is_contact = False

    @api.onchange('zip')
    def on_change_addr(self):
        if not self.zip:
            return {}
        pincode_details_obj = self.env['pincode.mapping'].sudo()
        if self.zip:
            details_id = pincode_details_obj.search([('pin_code','=',self.zip)])
            if details_id:
                city = details_id[0].city
                state_id = details_id[0].state.id
                other_id = pincode_details_obj.search([('locality','=','Other')])
                if not other_id:
                    other_id = pincode_details_obj.create({'locality':'Other','city':'dummy','pin_code':'dummy','state':'54'})
                return {'value':{'state_id':state_id,'city':city},'domain':{'locality_id':['|',('pin_code','=',self.zip),('id','=',other_id)]}}
        else:
            return {'value':{'state_id':False,'city':False},'domain':{'locality_id':[]}}

    @api.constrains('name_of_site')
    def _check_name(self):
        for rec in self:
            c_name = self.env['res.partner'].search([('name_of_site', '=ilike', rec.name_of_site), ('id', '!=', rec.id), ('partner_site_id', '=', rec.partner_site_id.id)])
            if c_name:
                raise ValidationError("Site Name already exists, please add unique name.")


class TransportLinks(models.Model):
    _name = 'transport.links'
    _description = "Transport Links"

    tp_type = fields.Selection([('mpls','MPLS'),('internet','Internet'),('lte','LTE')], string="Type")
    tp_bandwidth = fields.Char("Bandwidth")
    tp_sla = fields.Char('SLA')
    tp_media = fields.Selection([('fiber','Fiber'),('copper','Copper'),('microwave','Microwave')], string='Media')
    transport_link_id = fields.Many2one('res.partner', string='TP Partner')
    bandwidth_type = fields.Selection([
        ('kbps', 'Kbps'),
        ('mbps', 'Mbps'),
        ('gbps', 'Gbps')], string="Bandwidth Type", tracking=True)



class PincodeMapping(models.Model):
    _name = 'pincode.mapping'
    _description = "Pincode Mapping"
    _rec_name = "locality"

    pin_code = fields.Char('PIN code', required=True)
    city = fields.Char('City',required=True)
    state = fields.Many2one('res.country.state', 'State',required=True)
    locality =  fields.Char('Locality/Town', required=True)


class Bank(models.Model):
    _inherit = "res.partner.bank"

    bank_spoc_id = fields.Many2one('res.partner', domain=[('spoc_role', '=', 'bank_spoc')])


class ContactOtherDetail(models.Model):
    _name = "contact.other.detail"
    _description = 'Contact Other Detail'
    _rec_name = 'medium_id'

    org_contact_id = fields.Many2one('res.partner')
    medium_id = fields.Many2one('utm.medium')
    phone_code = fields.Char()
    medium_name = fields.Char(related='medium_id.name')
    medium_detail = fields.Char()
    is_preferred_contact = fields.Boolean(string='Preferred Contact')
    enable = fields.Boolean(string="Enabled")

# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2022 (https://www.in2ittech.com)
#
##############################################################################

import logging
from odoo import models, api, fields, exceptions
from odoo.exceptions import ValidationError
_logger = logging.getLogger(__name__)

import requests
import base64
from odoo import models, fields, api


class IrModel(models.Model):
    _inherit = 'ir.model'

    def _default_field_id(self):
        if self.env.context.get('from_api'):
            return []
        return super(IrModel, self)._default_field_id()

    from_api = fields.Boolean('Is Created from API?')
    description = fields.Char(string="Description")
    name = fields.Char(string="Table Name")
    created_by = fields.Char(string="Created By")
    table_type = fields.Selection([('is_standard', 'Standard'),('is_custom','Custom')], string='Table Type')
    field_id = fields.One2many('ir.model.fields', 'model_id', string='Fields', required=True, copy=True, default=_default_field_id)

    def get_records(self):
        model_name = self.sudo().model
        return {
            'type': 'ir.actions.act_window',
            'name': 'Records',
            'res_model': model_name,
            'view_type': 'list',
            'view_mode': 'list',
            'views': [[False, 'list'], [False, 'form']],
        }

    @api.constrains('model')
    def _check_model_name(self):
        for model in self:
            if not models.check_object_name(model.model):
                raise ValidationError(_("The model name can only contain lowercase characters, digits, underscores and dots."))

class IrModelFields(models.Model):
    _inherit = 'ir.model.fields'

    from_api = fields.Boolean('Is Created from API?')
    description = fields.Char(string="Description")
    is_unique = fields.Boolean('Unique')
    foreign_key = fields.Boolean('Foreign')
    limit_min = fields.Char(string="Min. Limit")
    limit_max = fields.Char(string="Max. Limit")
    primary_key = fields.Boolean('Primary Key')
    date_format = fields.Selection([('dd/mm/yyyy', 'DD/MM/YYYY'),('mm/dd/yyyy','MM/DD/YYYY')], string='Date Format')
    

class ProductDevices(models.Model):
    _inherit = 'product.template'
    _check_company_auto = True

    supported_devices_ids = fields.Many2many('product.template', 'product_supported_devices_rel', 'product_src_id', 'product_dest_id', string="Supported Devices")
    product_features_ids = fields.Many2many('product.features', string="Product Features")
    is_devices = fields.Boolean("Is Devices ?")
    is_cpe_models = fields.Boolean("Is CPE Models ?")

    # Product Offering Fields
    is_product_offering = fields.Boolean(string='Product Offering??')
    product_package = fields.Many2one('product.package', string='Product Package')
    last_mile = fields.Selection([('yes', 'Yes'),('no','No')], string="Last Mile")

    # Product /CPE OEM model
    oem_model_id = fields.Many2one('product.brands', string="OEM Model")

class IPAddressType(models.Model):
    _name = 'ip.address.type'
    _description = 'IP Address Type'

    name = fields.Char('Address Type')

class IPAddress(models.Model):
    _name = 'ip.address'
    _description = 'IP Address'

    name = fields.Char('IP Address')

class CPEType(models.Model):
    _name = 'cpe.type'
    _description = 'CPE Type'

    name = fields.Char('CPE TYPE')

class RoutingProtocol(models.Model):
    _name = 'routing.protocol'
    _description = 'Routing Protocol'

    name = fields.Char('Routing Protocol')

class IPSecTunnel(models.Model):
    _name = 'ip.sec.tunnel'
    _description = 'IP Sec. Tunnel'

    name = fields.Char('Name')
    is_url_filtering = fields.Selection([
        ('yes', 'Yes'), ('no', 'No')
    ], string='Url Filtering') 

class TransportLinkType(models.Model):
    _name = 'transport.link.type'
    _description = 'Transport Link Type'

    name = fields.Char('Name')

class MediaType(models.Model):
    _name = 'media.type'
    _description = 'Media Type'

    name = fields.Char('Name')

class SecurityService(models.Model):
    _name = 'security.service'
    _description = 'Security Service'
    _rec_name = "name"

    name = fields.Char('Name')
    is_malware_protecion = fields.Selection([
        ('yes', 'Yes'), ('no', 'No')
    ], string='Malware Protection')

    is_url_filtering = fields.Selection([
        ('yes', 'Yes'), ('no', 'No')
    ], string='Url Filtering')

    is_intrusion_prevention = fields.Selection([
        ('yes', 'Yes'), ('no', 'No')
    ], string='Intrusion Prevention')

    is_local_attack_defence = fields.Selection([
        ('yes', 'Yes'), ('no', 'No')
    ], string='Local Attack Defence')


class ResourceSpecification(models.Model):
    _name = 'resource.specification'
    _description = 'Resource Specification'
    _rec_name = "name"

    name = fields.Char(string="Name/ID")
    customer_permise_router_id = fields.Many2one('cpe.type', string="Customer Permise Router")
    router_target = fields.Char(string="Router Target")
    fec = fields.Char(string="FEC")
    ip_address = fields.Many2one('ip.address', string="IP Address")
    ip_address_type = fields.Many2one('ip.address.type', string="IP Address Type")
    auth_profile = fields.Char(string="Auth Profile")


class ServiceSpecification(models.Model):
    _name = 'service.specification'
    _description = "Service Specification"
    _rec_name = "name"

    name = fields.Char(string="Name/Service ID")
    tp_configuration = fields.Many2one('transport.link.type', string="Transport Link Configuration")
    routing_configuration = fields.Many2one('routing.protocol', string='Routing Configuration')
    product_optimization_service = fields.Char(string="Product Optimization Service")
    duplication_compression = fields.Char(string='De-Duplication and Compression')
    security_service =  fields.Many2one('security.service',string='Security Service')
    ip_sec_tunnel = fields.Many2one('ip.sec.tunnel', string='IP-SEC Tunnel')


class Devices(models.Model):
    _name = 'product.devices'
    _description = "Product Devices"
    _rec_name = "name"

    name = fields.Char(string='Device ID')
    tp_type = fields.Many2one('transport.link.type', string="Transport Link Type")
    cpe_type = fields.Many2one('cpe.type', string='CPE Type')
    cpe_model = fields.Many2many('product.template', string="CPE Model's")
    routing = fields.Many2one('routing.protocol', string='Routing')
    optimization = fields.Char(string='Optimization')

class ProductSpecification(models.Model):
    _name = 'product.specification'
    _description = "Product Specification"
    _rec_name = "name"

    name = fields.Char(string="Name/ID")
    device = fields.Many2one('product.devices', string="Device")
    security = fields.Many2one('security.service', string="Security")

class ProductPackage(models.Model):
    _name = 'product.package'
    _description = "Product Package"
    _rec_name = "name"

    name = fields.Char(string="Package ID")
    product_specification = fields.Many2one('product.specification', string="Product Specification")
    service_specification = fields.Many2one('service.specification', string="service Specification")
    resource_specification = fields.Many2one('resource.specification', string="Resource Specification")

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    _description = "Sale Order Line Extra  Fields"

    properties = fields.Selection([
        ('cloud', 'Cloud'), ('physical', 'Physical')
    ], string='Properties')
    frequency_type = fields.Selection([
        ('nrc', 'NRC'), ('mrc', 'MRC'), ('yrc', 'YRC')
    ], string='Frequency Type')
    frequency_count = fields.Integer(string='Frequency Count')
    tax_value = fields.Float(related='tax_id.amount',string='Tax Value')
    tax_type = fields.Selection(related='tax_id.type_tax_use',string='Tax Type')
    discount_type = fields.Selection([('standard', 'Standard'), ('none', 'None')], string='Discount Type')


class Product(models.Model):
    _inherit = "product.product"
    _description = "Product product"

    topology_type = fields.Selection([
        ('hub_spoke', 'Hub & Spoke '),
        ('full_mesh', 'Full Mesh'),
        ('partial_mesh', 'Partial Mesh')
    ], string="Topology Type")

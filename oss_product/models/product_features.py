# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2022 (https://www.in2ittech.com)
#
##############################################################################

import logging
from random import randint
from odoo import models, api, fields, exceptions

_logger = logging.getLogger(__name__)

import requests
import base64
from odoo import models, fields, api

class ProductFeatures(models.Model):
    _name = 'product.features'
    _description = "Product Features"
    _order = "name"

    def _default_color(self):
        return randint(1, 11)

    name = fields.Char(string="Name")
    description = fields.Text(string="Description")
    color = fields.Integer('Color', default=_default_color)
    image_1920 = fields.Image("Image")


class ProductBrands(models.Model):
    _name = "product.brands"
    _description = "Product Brands"

    name = fields.Char(string='Brand Name', required=True)
    product_count = fields.Integer(string='Total Count')
    brand_logo = fields.Binary()


#  EXtra table
class ProductFamilyCategory(models.Model):
    _name = "oss_product.family.category"
    _description = "Product Family Category"

    name = fields.Char(string='Category', required=True)
    description = fields.Char(string="Category Description", required=True)


class ProductFamilyType(models.Model):
    _name = "oss_product.family.type"
    _description = "Product Family Type"

    name = fields.Char(string='Type', required=True)
    description = fields.Char(string="Type Description", required=True)

class ProductFamily(models.Model):
    _name = "oss_product.family"
    _description = "Product Family"

    name = fields.Char(string='Family Name', required=True)
    description = fields.Char(string="Description", required=True)
    category = fields.Many2one("oss_product.family.category", string="Category")
    ptype = fields.Many2one("oss_product.family.type", string="Type")
    image = fields.Binary(string="Image")



class ProductGroupCategory(models.Model):
    _name = "oss_product.group.category"
    _description = "Product Group Category"

    name = fields.Char(string='Category', required=True)
    description = fields.Char(string="Category Description", required=True)

class ProductGroupType(models.Model):
    _name = "oss_product.group.type"
    _description = "Product Group Type"

    name = fields.Char(string='Type', required=True)
    description = fields.Char(string="Type Description", required=True)

class OSSProduct(models.Model):
    _name = "oss.product"
    _description = "OSS Product"

    name = fields.Char(string='Product Name', required=True)
    description = fields.Char(string="Product Description")
    family_name = fields.Many2one('oss_product.family', string="Family Name")
    category  = fields.Char(string="Category")
    ptype = fields.Char(string='Type')
    # group_name = fields.Many2one('oss_product.group', string='Group Name')
    product_picture = fields.Binary(string="Product Picture")

class ProductGroup(models.Model):
    _name = "oss_product.group"
    _description = "Product Group"

    name = fields.Char(string='Group Name', required=True)
    description = fields.Char(string="Product Group Description")
    family_name = fields.Many2one('oss_product.family', string="Family Name")
    category = fields.Many2one('oss_product.group.category', string="Category")
    ptype = fields.Many2one('oss_product.group.type', string="Type")
    picture = fields.Binary(string="Image")
    location = fields.Many2one('oss.location', string='Location')



class OssLocation(models.Model):
    _name = "oss.location"
    _description = "OSS Location"
    _rec_name = "street"

    # name = fields.Char(string='Name', required=True)
    street = fields.Char(string="Street", required=True)
    country = fields.Many2one('res.country', string="Country", required=True)
    province_state = fields.Many2one('res.country.state', string="Province_State")
    city = fields.Char(string="City")
    zip_code = fields.Char(string="Zip Code")


class OssVarient(models.Model):
    _name = "oss.varient"
    _description = "OSS Varient"
    _rec_name ="varient"

    product = fields.Many2one('oss.product', string="Product")
    varient = fields.Char(string='Varient', required=True)
    description = fields.Char(string="Description")
    vtype = fields.Char(string="Type")
    category = fields.Char(string="Category")

    # is_stock = fields.Boolean(string='Is Stock')
    # stock_available = fields.Integer(string="Stock Available")

class VarientConfigGroup(models.Model):
    _name = "oss_varient.config.group"
    _description = "Varient Config Group"
    _rec_name = "variant_config_name"

    variant_config_name = fields.Char(string="Variant Config. Name")
    variant = fields.Many2many('oss.varient', string="Varient")
    vgtype = fields.Char(string="Type")
    category = fields.Char(string="Category")

class ConfigItem(models.Model):
    _name = "oss_config.item"
    _description = "Config Item"
    _rec_name = "config_item"

    config_item = fields.Char(string="Config Item", required="True")
    description = fields.Char(string="Description") 
    varient_config = fields.Many2one('oss_varient.config.group', string="Variant Config. Name")
    parameter_type = fields.Char(string="Parameter Type")
    measurement_unit = fields.Char(string="Measurement Unit")
    is_priced = fields.Boolean(string="Is Priced")
    currency_unit = fields.Char(string="Currency Unit")
    unit_price = fields.Char(string="Unit Price")
    minimun_limit = fields.Char(string="Minimun Limit")
    maximum_limit = fields.Char(string="Maximum Limit")
    included_in_base_price = fields.Char(string="Included in Base Price")
    renewable = fields.Char(string="Renewable")
    renew_frequency = fields.Char(string="Renew Frequency")

class ConfigOptions(models.Model):
    _name = "oss_config.options"
    _description = "Config Options"
    _rec_name = "configuration_options"

    configuration_options = fields.Char(string="Configuration Options", required="True")
    config_item = fields.Many2one('oss_config.item', string="Config Item")

class ServiceComponetConfigOptions(models.Model):
    _name = "oss_service.componet.options"
    _description = "Service Componet Config Options"
    _rec_name = "name"

    name = fields.Char(string="Name")
    varient = fields.Many2one('oss.varient', string="Varient")
    config_item = fields.Many2one('oss_config.item', string="Config Item")
    metric = fields.Char(string="Metric")
    config_options = fields.Char(string="Config Options")
    routers = fields.Char(string="Routers")


class DeviceConfigOptions(models.Model):
    _name = "oss_device.config.options"
    _description = "Device Config Options"
    _rec_name = "oem"

    oem = fields.Char(string="OEM")
    series = fields.Char(string="Series")
    model_name = fields.Char(string="Model")
    description = fields.Char(string="Description")
    supported_product_family = fields.Many2one('oss_product.family', string="Supported Product Family")
    category = fields.Char(string='Category')
    dtype = fields.Char(string="Type")
    product_picture = fields.Binary(string="Product Picture")


class VarientConfig(models.Model):
    _name = "oss_varient.config"
    _description = "Varient Config"

    name = fields.Char(string='Name', required=True)
    varient = fields.Many2one('oss.varient', string="Varient")
    config_name = fields.Many2one('oss_config.item.list',string="Config Name")
    is_priced = fields.Boolean(string="Is_Priced")
    currency_unit = fields.Many2one('oss.currency', string="Currency Unit")
    unit_price = fields.Float(string="Unit Price")
    discount_name = fields.Many2one('oss_discount.master', string="Discount Name")
    measurement_unit = fields.Char(string='Measurement Unit')
    tax_id = fields.Many2one('oss.tax', string="Tax ID")
    renewable = fields.Boolean(string="Renewable")
    renew_frequency = fields.Char(string="Renew Frequency")


class ProductConfig(models.Model):
    _name = "oss_product.config"
    _description = "Oss Product Config"

    name = fields.Char(string='Name', required=True)
    product = fields.Many2one('oss.product', string="Product")
    config_name = fields.Many2one('oss_config.item.list', string="Config Name")
    is_priced = fields.Boolean(string="Is_Priced")
    currency_unit = fields.Float(string="Currency Unit")
    unit_price = fields.Float(string="Unit Price")
    discount_name = fields.Many2one('oss_discount.master', string="Discount Name")



class ConfigItemList(models.Model):
    _name = "oss_config.item.list"
    _description = "Config Item List"

    name = fields.Char(string='Config Name', required=True)
    description = fields.Char(string="Description")
    ctype = fields.Char(string="Type")
    is_priced = fields.Boolean(string="Is_Priced")
    currency_unit = fields.Many2one('oss.currency', string="Currency Unit")
    unit_price = fields.Float(string="Unit Price")
    measurement_unit = fields.Char(string="Measurement Unit")


class DiscountCategory(models.Model):
    _name = "oss_discount.category"
    _description = "Discount Category"

    name = fields.Char(string='Category', required=True)
    description = fields.Char(string="Description")

class DiscountMaster(models.Model):
    _name = "oss_discount.master"
    _description = "Discount Master"

    name = fields.Char(string='Discount Name', required=True)
    category = fields.Many2one('oss_discount.category', string="Category")
    dtype = fields.Char(string="Type")
    value = fields.Integer(string="Value")



class OssCurrency(models.Model):
    _name = "oss.currency"
    _description = "Oss Currency"

    name = fields.Char(string='Currency Unit', required=True)

class OssTax(models.Model):
    _name = "oss.tax"
    _description = "Tax Table"

    name = fields.Char(string='Tax Name', required=True)
    tax_type = fields.Char(string="Tax Type")
    location = fields.Many2one('oss.location', string="Location")
    Value_percent = fields.Float(string="Value")
    
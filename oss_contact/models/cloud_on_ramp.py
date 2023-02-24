# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2022 (https://www.in2ittech.com)
#
##############################################################################
from datetime import datetime
import logging
from odoo import models, api, fields, exceptions
from lxml import etree

from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class CloudOnRamp(models.Model):
    _name = 'cloud.ramp'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Cloud On Ramp'

    name = fields.Char(string="CoR Site Name", required=True, tracking=True)
    provider_name  = fields.Selection([
        ('transit_vet', 'Transit vNET(Azure)'),
        ('vpc_aws', 'VPC(AWS)')
    ], string="Provider Name", required=True, tracking=True)
    transit_wan_edge  = fields.Char(string="Transit WAN Edge", tracking=True)
    cor_city = fields.Char(string="City", tracking=True)
    cor_zip = fields.Char(string="Zip", tracking=True)
    cor_state = fields.Many2one('res.country.state', string="State", tracking=True)
    cor_country = fields.Many2one('res.country', string="Country", tracking=True)
    redundency_id = fields.Many2many('cloud.ramp.redundency', string='Redundency', tracking=True)
    site_spoc_fname = fields.Char(string="Site SPOC First Name", tracking=True)
    site_spoc_lname = fields.Char(string="Site SPOC Last Name", tracking=True)
    cor_country_code = fields.Char(string="Country Code", tracking=True)
    site_spoc_phone = fields.Char(string="Site SPOC Phone", tracking=True)
    site_spoc_email = fields.Char(string="Site SPOC Email", tracking=True)
    bandwidth = fields.Integer(string="Bandwidth", tracking=True)
    bandwidth_type = fields.Selection([
        ('kbps', 'Kbps'),
        ('mbps', 'Mbps'),
        ('gbps', 'Gbps')], string="Bandwidth Type", tracking=True)
    total_liscenses  = fields.Integer(string="Total Liscenses Required", tracking=True)
    location_a_end  = fields.Char(string="Location A End", tracking=True)
    lead_id = fields.Many2one("crm.lead", string="Lead", tracking=True)
    active = fields.Boolean(default=True, help="Set active to false to hide the Cloud on Ramp without removing it.")

    @api.constrains('name')
    def _check_name(self):
        for rec in self:
            c_name = self.env['cloud.ramp'].search([('name', '=ilike', rec.name), ('id', '!=', rec.id), ('lead_id', '=', rec.lead_id.id)])
            if c_name:
                raise ValidationError("CoR Site Name already exists, please add unique name.")

class CloudOnRampRedundency(models.Model):
    _name = 'cloud.ramp.redundency'
    _description = 'Cloud On Ramp Redundency'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True, help="Set active to false to hide the CoR Redundency without removing it.")


class MailTracking(models.Model):
    _inherit = 'mail.tracking.value'

    @api.model
    def create_tracking_values(self, initial_value, new_value, col_name, col_info, tracking_sequence, model_name):
        tracked = True

        field = self.env['ir.model.fields']._get(model_name, col_name)
        if not field:
            return

        values = {'field': field.id, 'field_desc': col_info['string'], 'field_type': col_info['type'], 'tracking_sequence': tracking_sequence}

        if col_info['type'] in ['integer', 'float', 'char', 'text', 'datetime', 'monetary']:
            values.update({
                'old_value_%s' % col_info['type']: initial_value,
                'new_value_%s' % col_info['type']: new_value
            })
        elif col_info['type'] == 'date':
            values.update({
                'old_value_datetime': initial_value and fields.Datetime.to_string(datetime.combine(fields.Date.from_string(initial_value), datetime.min.time())) or False,
                'new_value_datetime': new_value and fields.Datetime.to_string(datetime.combine(fields.Date.from_string(new_value), datetime.min.time())) or False,
            })
        elif col_info['type'] == 'boolean':
            values.update({
                'old_value_integer': initial_value,
                'new_value_integer': new_value
            })
        elif col_info['type'] == 'selection':
            values.update({
                'old_value_char': initial_value and dict(col_info['selection']).get(initial_value, initial_value) or '',
                'new_value_char': new_value and dict(col_info['selection'])[new_value] or ''
            })
        elif col_info['type'] == 'many2one':
            values.update({
                'old_value_integer': initial_value and initial_value.id or 0,
                'new_value_integer': new_value and new_value.id or 0,
                'old_value_char': initial_value and initial_value.sudo().name_get()[0][1] or '',
                'new_value_char': new_value and new_value.sudo().name_get()[0][1] or ''
            })
        elif col_info['type'] == 'many2many':
            old_value_char = ""
            new_value_char = ""
            for initial_value_id in initial_value:
                old_value_char +=  initial_value_id.sudo().name_get()[0][1] + ' ' +','
            for new_value_id in new_value:
                new_value_char +=  new_value_id.sudo().name_get()[0][1] + ' ' + ','
            values.update({
                'old_value_char': initial_value and old_value_char[:-1] or '',
                'new_value_char': new_value and new_value_char[:-1] or '',
            })
            if tracked:
                return values
        else:
            tracked = False
        if tracked:
            return values
        return {}

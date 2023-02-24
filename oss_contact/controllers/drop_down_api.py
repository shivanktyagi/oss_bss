# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2022 (https://www.in2ittech.com)
#
##############################################################################

import logging
import odoo
import json
import odoo.modules.registry
from odoo.tools.translate import _
from odoo import http, tools, fields
from datetime import datetime
import datetime 
import re
import base64
import requests
from odoo.exceptions import ValidationError
from odoo.http import content_disposition, dispatch_rpc, request, Response

_logger = logging.getLogger(__name__)

def _get_selection_list(model, field_name):
	res = []
	partner_obj = request.env[model].sudo()
	for i in partner_obj._fields[field_name].selection:
		res.append({'id':i[0],'name':i[1]})
	return res

class LeadPageDropDown(http.Controller):
	@http.route('/api/lead_page/dropdown', methods=["GET"], auth="none")
	def lead_page_dropdown(self, **kwargs):
		lead_page_list = []
		source_list = [] 
		product_list = []
		certainity_list = []
		source_obj = request.env['utm.source'].sudo().search([])
		certainity_obj = request.env['crm.certainity'].sudo().search([])
		product_objs = request.env['product.product'].sudo().search([('sale_ok', '=', True),('is_cpe_models', '=', True)])
		security_obj_ids = request.env['security.requirement'].sudo().search([])
		cor_redundency_ids = request.env['cloud.ramp.redundency'].sudo().search([])

		# Source Logic
		for source_id in source_obj:
			vals = {'id': source_id.id, 'name': source_id.name if source_id.name else ''}
			source_list.append(vals)

		# Product 
		for product_id in product_objs:
			vals = {'id': product_id.id, 'name': product_id.display_name if product_id.display_name else ''}
			product_list.append(vals)

		# Certainity
		for certainity_id in certainity_obj:
			vals = {'id': certainity_id.id, 'name': certainity_id.name if certainity_id.name else ''}
			certainity_list.append(vals)

		security_requirement_list =[]
		for security_id in security_obj_ids:
			security_requirement_list.append(security_id.name)

		cor_redundency_list =[]
		for cor_redundency_id in cor_redundency_ids:
			cor_redundency_list.append(cor_redundency_id.name if cor_redundency_id.name else '')

		lead_page_dict = {
			"source" : source_list,
			"products": product_list,
			"purchase_process": _get_selection_list('crm.lead', 'purchase_process'),
			"existing_routing_protocol": _get_selection_list('crm.lead', 'existing_routing_protocol'),
			"internet_required": _get_selection_list('res.partner', 'site_internet_usage'),
			"site_type": _get_selection_list('res.partner', 'site_type'),
			"hosting_models": _get_selection_list('res.partner', 'hosting_models'),
			"redundancy_requirement": _get_selection_list('res.partner', 'redundancy_requirement'),
			"provider_name": _get_selection_list('cloud.ramp', 'provider_name'),
			"topology": _get_selection_list('crm.lead', 'topology_requirement'),
			"public_cloud_name": _get_selection_list('crm.lead', 'public_cloud_name'),
			"application_qos_parameter": _get_selection_list('app.modeling', 'application_qos_parameter'),
			"security_requirement": security_requirement_list,
			"cor_redundancy": cor_redundency_list,
			"application_priority": _get_selection_list('app.modeling', 'application_priority'),
			"application_hosted":_get_selection_list('app.modeling', 'application_hosted'),
			"billing_cycle": _get_selection_list('crm.lead', 'billing_cycle'),
			"contact_duration" : _get_selection_list('crm.lead', 'contract_duration'),
			"tp_link_type" : _get_selection_list('transport.links', 'tp_type'),
			"tp_link_media" : _get_selection_list('transport.links', 'tp_media'),
			"bandwidth_type": _get_selection_list('cloud.ramp','bandwidth_type'),
			"certainity": certainity_list
		}

		lead_page_list.append(lead_page_dict)
		return Response(json.dumps(lead_page_list), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")

	@http.route('/api/lead/cpe_oem_model_dropdown', methods=["GET"], auth="none")
	def cpe_oem_model_dropdown(self, **kwargs):
		oem_model = []
		product_oem_ids = request.env['product.brands'].sudo().search([])
		for oem_id in product_oem_ids:
			vals = {"id":oem_id.id , "name":oem_id.name if oem_id.name else ''}
			oem_model.append(vals)
		return Response(json.dumps(oem_model), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")


	@http.route('/api/lead/cpe_details_dropdown', methods=["GET"], auth="none")
	def cpe_details_dropdown(self, **kwargs):
		cpe_details = []
		product_ids = request.env['product.product'].sudo().search([('sale_ok', '=', True),('is_cpe_models', '=', True)])
		for product_id in product_ids:
			product_values = {
				'id': product_id.id,
				'name': product_id.display_name if product_id.display_name else '',
				'oem_id': product_id.oem_model_id.id if product_id.oem_model_id and product_id.oem_model_id.id else ''
				}
			cpe_details.append(product_values)

		return Response(json.dumps(cpe_details), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")

	@http.route('/api/lead/progress_bar', methods=["GET"], auth="none")
	def lead_progress_bar(self, **kw):
		progress_bar = [{"id": "qualify", "name": "Qualify"},{"id": "develop", "name": "Develop"},{"id": "propose", "name": "Propose"}, {"id": "deliver", "name": "Deliver"}]
		return Response(json.dumps(progress_bar), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")

	

	@http.route('/api/global/dropdown', methods=["GET"], auth="none")
	def api_global_dropdown(self, **kw):
		data = request.params.copy()
		model = data.get('model')
		field_name = data.get('field_name')
		field_obj = request.env['ir.model.fields'].sudo().search([('name','=',field_name),('model_id','=',model)])
		result = {}
		print(model)
		print(field_obj.ttype)
		if field_obj.ttype == 'selection':
			result[field_name] = _get_selection_list(model, field_name)
		# elif field_obj.ttype in ['one2many','many2many']:
		# 	model_obj = request.env['ir.model'].sudo().search([('model','=',model)])
		return Response(json.dumps(result), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")

class GeneralDetailsDropDown(http.Controller):
	@http.route('/api/general_details/dropdown', methods=["GET"], auth="none")
	def general_details_dropdown(self, **kwargs):
		general_details = []
		product_objs = request.env['product.product'].sudo().search([('sale_ok', '=', True),('is_cpe_models', '=', True)])
		cpe_model = []
		for product_id in product_objs:
			vals = {'id': product_id.id, 'name': product_id.display_name if product_id.display_name else ''}
			cpe_model.append(vals)
		general_details_dict = {
			'existing_routing_protocol': _get_selection_list('crm.lead', 'existing_routing_protocol'),
			'site_internet_usage': _get_selection_list('res.partner', 'site_internet_usage'),
			'cpe_model_ids' : cpe_model,
		}
		general_details.append(general_details_dict)
		return Response(json.dumps(general_details), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")

class SiteDetailsDropDown(http.Controller):
	@http.route('/api/site_details/dropdown', methods=["GET"], auth="none")
	def site_details_dropdown(self, **kwargs):
		site_details = []
		product_objs = request.env['product.product'].sudo().search([('sale_ok', '=', True),('is_cpe_models', '=', True)])
		hardware_router = []
		for product_id in product_objs:
			vals = {'id': product_id.id, 'name': product_id.display_name if product_id.display_name else ''}
			hardware_router.append(vals)
		site_details_dict = {
			'site_type': _get_selection_list('res.partner', 'site_type'),
			'hosting_models': _get_selection_list('res.partner', 'hosting_models'),
			'redundancy_requirement' : _get_selection_list('res.partner', 'redundancy_requirement'),
			'hardware_router': hardware_router,
			'internet_usage': _get_selection_list('res.partner', 'site_internet_usage'),
		}
		site_details.append(site_details_dict)
		return Response(json.dumps(site_details), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")

class ApplicationDropDown(http.Controller):
	@http.route('/api/application_details/dropdown', methods=["GET"], auth="none")
	def application_details_dropdown(self, **kwargs):
		application_details = []
		application_details_dict = {
			'application_hosted': _get_selection_list('app.modeling', 'application_hosted'),
			'application_priority': _get_selection_list('app.modeling', 'application_priority'),
		}
		application_details.append(application_details_dict)
		return Response(json.dumps(application_details), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")


class CancelLeadReasonDropDown(http.Controller):
	@http.route('/api/cancel_lead_reason/dropdown', methods=["GET"], auth="none")
	def cancel_lead_reason_dropdown(self, **kwargs):
		crm_lost_reason_obj = request.env['crm.lost.reason'].sudo().search([])
		lost_reason = []
		for lose_reason_id in crm_lost_reason_obj:
			lost_reason.append((lose_reason_id.stage_ids.name if lose_reason_id.stage_ids and lose_reason_id.stage_ids.name else '',
								lose_reason_id.id if lose_reason_id.id else '', 
								lose_reason_id.name if lose_reason_id.name else ''))
		return Response(json.dumps(lost_reason), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")


class PincodeMappingDropDown(http.Controller):
	@http.route('/api/pincode_mapping/dropdown', methods=['GET'], auth="none")
	def pincode_mapping_dropdown(self, **kwargs):
		pincode_mapping_obj = request.env['pincode.mapping'].sudo()
		pincode_mapping = []
		for pincode in pincode_mapping_obj.search([]):
			vals = {
				"id": pincode.id if pincode.id else '',
				"pin_code": pincode.pin_code if pincode.pin_code else '',
				"city": pincode.city if pincode.city else '',
				"state": pincode.state.id if pincode.state else '',
				"locality": pincode.locality if pincode.locality else '',
			}
			pincode_mapping.append(vals)
		return Response(json.dumps(pincode_mapping), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")


class PropertyAttributeDropdown(http.Controller):
	@http.route('/api/attribute_property/dropdown', methods=['GET'], auth="none")
	def api_attribute_property_dropdown(self, **kwargs):
		attribute_property = [{"id": "primary_key", "name": "Primary Key", },
				{"id": "foreign_key", "name": "Foreign Key", },
				{"id": "is_unique", "name": "Unique", },
				{"id": "index", "name": "Index", },
				{"id": "required" , "name": "Mandatory"}]
		return Response(json.dumps(attribute_property), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")

	@http.route('/api/data_type/dropdown', methods=['GET'], auth="none")
	def api_data_type_dropdown(self, **kwargs):
		data_types = [{"id":key, "name":key.capitalize()} for key in sorted(fields.Field.by_type) if key not in ['many2many','many2one','many2one_reference','one2many','selection']]
		return Response(json.dumps(data_types), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")

	@http.route('/api/selected_table/dropdown', methods=['GET'], auth="none")
	def api_table_dropdown(self, **kwargs):
		dynamic_tables = request.env['ir.model'].sudo().search([('from_api','=',True)])
		dynamic_table_lists = [{"id":table.id , "name":table.name} for table in dynamic_tables]
		return Response(json.dumps(dynamic_table_lists), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")

	@http.route('/api/relationship/dropdown', methods=['GET'], auth="none")
	def api_relationship_dropdown(self, **kwargs):
		data_types = [{"id":key, "name":key.capitalize()} for key in sorted(fields.Field.by_type) if key in ['many2many','many2one','one2many']]
		return Response(json.dumps(data_types), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")

	@http.route('/api/date_format/dropdown', methods=['GET'], auth="none")
	def api_date_format_dropdown(self, **kwargs):
		date_formats = [{"id":"dd/mm/yyyy","name":"DD/MM/YYYY"}, {"id":"mm/dd/yyyy" , "name":"MM/DD/YYYY"}]
		return Response(json.dumps(date_formats), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")
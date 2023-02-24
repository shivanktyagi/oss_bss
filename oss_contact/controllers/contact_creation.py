# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2022 (https://www.in2ittech.com)
#
##############################################################################
import csv
import logging
import odoo
import json
from odoo import http
import base64
import requests
from odoo.http import request, Response
from datetime import datetime
from odoo.exceptions import AccessError, MissingError
_logger = logging.getLogger(__name__)

FIELD_OPERATORS = {
	"is true": "=",
	"is false": "!=",
	"contains": "ilike",
	"does not contain": "not ilike",
	"is equal to": "=",
	"is not equal to": "!=",
	"is set": "!=",
	"is not set": "=",
	"is after": ">",
	"is before": "<",
	"is after or equal to": ">=",
	"is before or equal to": "<=",
	"is between": "between",
	"greater than": ">",
	"less than": "<",
	"greater than or equal to": ">=",
	"less than or equal to": "<=",
	"is": "=",
	"is not": "!=",
	"in": "in",
}

def _error_403(error_msg):
	return {
		'success': False,
		'status': 'Already exists',
		'code': 403,
		'response': error_msg
	}

def _error_400(error_msg):
	return {
		'success': False,
		'status': 'Bad Request.',
		'code': 400,
		'response': error_msg
	}

def _success_200(success_msg, vals):
	return {
		'success': True,
		'status': success_msg,
		'code': 200,
		'payload':vals
	}
def _success_organization_200(success_msg, vals):
	return {
		'success': True,
		'response': success_msg,
	}
def _success_organization_error_200(error_msg, vals):
	return {
		'success': False,
		'response': error_msg,
	}

def _get_filter_domain(filter_list):
	domain = []
	for val in filter_list:
		if len(filter_list) > 1 and filter_list.index(val) >=1:
			if val.get('logical') == 'or':
				domain = [('|')] + domain
			if val.get('logical') == 'and':
				domain = [('&')] + domain
		if val.get('select_rule') :
			if FIELD_OPERATORS.get(val.get('select_rule')) == 'between' and (val.get('from_value') or val.get('to_value')):
				domain += ['&',(val.get('filter_by'), '>=',val.get('from_value')),(val.get('filter_by'), '<=',val.get('to_value'))]
			elif FIELD_OPERATORS.get(val.get('select_rule')) == 'in' and val.get('dropdown_value'):
				domain += [(val.get('filter_by'), 'in',val.get('dropdown_value'))]
			else:
				if FIELD_OPERATORS.get(val.get('select_rule')):
					domain += [(val.get('filter_by'), FIELD_OPERATORS.get(val.get('select_rule')),val.get('enter_value'))]
	return domain

class CheckDuplicateLead(http.Controller):
	@http.route('/api/check_duplicate_lead', methods=["GET"], auth="none")
	def check_duplicate_lead(self, **kwargs):
		partner_obj = request.env['res.partner'].sudo()
		lead = request.env['crm.lead'].sudo()
		if 'contact_number' in kwargs.keys():
			partner_id = partner_obj.search([('mobile', '=ilike', kwargs["contact_number"]),('active','=',True)],limit=1)
		else :
			partner_id = partner_obj.search([('email','=ilike', kwargs["email"]),('active','=',True)], limit=1)	
		if partner_id:
			existing_leads = lead.search([('partner_id','=',partner_id.id),('product_ids','in', int(kwargs["product_id"])),('active','=',True)])
			if existing_leads:
				vals = {
					'success': True,
					'status': 'User Already Exists.',
					'code': 204,
					'case_id': existing_leads[0].case_id,
					# 'lead_id': existing_leads[0].lead_number
					}
				return Response(json.dumps(vals), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")
			else:
				vals = {
					'success': True,
					'status': 'New Customer',
					'code': 200
				}
				return Response(json.dumps(vals), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")
		else:
			vals = {
				'success': True,
				'status': 'New Customer',
				'code': 200
			}
			return Response(json.dumps(vals), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")

class ContactCreate(http.Controller):

	@http.route('/api/contact_create', auth='public', csrf=False, type='json', methods=['POST'])
	def lead_create_contact(self, **kwargs):
		data = request.jsonrequest
		lead_obj = request.env['crm.lead'].sudo()
		customer_object = request.env['res.partner'].sudo()
		product_obj = request.env['product.template'].sudo()
		product_obj_id  = product_obj.search([('id','=',int(data.get('product'))),('active','=',True)],limit=1)
		if not product_obj_id:
			return _error_400("Product Not Found!")

		contact_vals = {
			"name": data.get("organization_name"),
			"designation": data.get("designation"),
			"department": data.get("department"),
			"spoc_name": data.get("first_name"),
			"spoc_lname": data.get("last_name"),
			"industry_id": data.get("industry"),
			"organization_registration": data.get("registration_number"),
			"street": data.get("organization_street1"),
			"street2": data.get("organization_street2"),
			"country_id": data.get("organization_country"),
			"state_id": data.get("organization_state"),
			"city": data.get("organization_city"),
			"zip": data.get("postal_code"),
			"mobile": data.get("contact_number"),
			"email": data.get("email"),
			"is_contact": 't',
			"company_type": 'company',
		}
		source_id = request.env['utm.source'].sudo().search([('name','=',"Portal Enquiry"),('active','=',True)]).id
		partner_id = customer_object.create(contact_vals)
		if partner_id:
			lead_vals = {
				"name": product_obj_id.name.replace(',', '',1),
				"partner_id": partner_id.id,
				"stage_id": 1,
				"product_ids": [(6,0,product_obj_id.ids)],
				"source_id": source_id
				}
			lead_id = lead_obj.with_context({
				'default_type': 'lead',
				'search_default_type': 'lead',
				'search_default_to_process': 1
			}).create(lead_vals)
			if lead_id :
				template_id = request.env.ref('oss_contact.mail_template_enquiry_crm_lead')
				email_context = request.env.context.copy()
				email_context.update({
					'email_to': partner_id.email,
					'crm_enquiry_id' : lead_id.case_id,
					'enquiry_product': lead_id.product_ids.ids,
					'csp_name': partner_id.name,
				})
				if template_id:
					template_id.with_context(email_context).sudo().send_mail(lead_id.id, True)
				return {
					'success': True,
					'status': 'Lead Created.',
					'code': 200,
					'response': partner_id.id,
					'case_id': lead_id.case_id,
					'lead_id': lead_id.id
				}
			else:
				return _error_400("Lead Not Created.")
		else:
			return _error_400("Lead Not Created.")


	@http.route('/api/create_linked_lead', auth='public', csrf=False, type='json', methods=['POST'])
	def api_linked_lead(self, **kw):
		data = request.jsonrequest
		lead_id = data.get('lead_id')
		product_id = data.get('product')
		source_id = request.env['utm.source'].sudo().search([('name','=',"Cross Sales"),('active','=',True)],limit=1).id
		lead_obj = request.env['crm.lead'].sudo()
		product_obj = request.env['product.product'].sudo()
		if lead_id and product_id:
			lead = lead_obj.search([('id','=',lead_id),('active','=',True)],limit=1)
			if not lead:
				return _error_400("Lead Id Not Found")
			product = product_obj.search([('id','=',product_id),('active','=',True)],limit=1)
			if not product:
				return  _error_400("Product Not Found")
			try:
				lead_vals = {
					"name": product.name,
					"partner_id": lead.partner_id.id,
					"stage_id": 1,
					"product_ids": [(6,0,product.product_tmpl_id.ids)],
					"parent_id": lead.id,
					"source_id": source_id
				}
				new_lead_id = lead_obj.with_context({
					'default_type': 'lead',
					'search_default_type': 'lead',
					'search_default_to_process': 1
				}).sudo().create(lead_vals)
				if new_lead_id:
					template_id = request.env.ref('oss_contact.mail_template_enquiry_crm_lead')
					email_context = request.env.context.copy()
					email_context.update({
						'email_to': new_lead_id.partner_id.email,
						'crm_enquiry_id' : new_lead_id.case_id,
						'enquiry_product': new_lead_id.product_ids.ids,
						'csp_name': new_lead_id.partner_id.name,
					})
					if template_id:
						template_id.with_context(email_context).sudo().send_mail(new_lead_id.id, True)
					return {
						'success': True,
						'status': 'New Lead Created.',
						'code': 200,
						'response': lead.partner_id.id,
						'case_id': new_lead_id.case_id,
						'lead_id': new_lead_id.id,
						"parent": lead.id,
					}
				else:
					return _error_400('Linked not Lead Created.')
			except Exception as e:
				return _error_400("Linked Lead Not Created." + str(e))
		else:
			return  _error_400("Invalid request payload. ")

	@http.route('/api/create_direct_lead', auth='public', csrf=False, type='json', methods=['POST'])
	def api_direct_lead(self, **kw):
		data = request.jsonrequest
		product_id = data.get('product')
		lead_id = data.get('lead_id')		
		lead_obj = request.env['crm.lead'].sudo()
		product_obj = request.env['product.product'].sudo()
		product = product_obj.search([('id','=',product_id),('active','=',True)],limit=1)
		dummy_user = request.env.ref('oss_contact.partner_dummy_user').sudo()
		if not product:
			return  _error_400("Invalid request payload")
		try:
			if lead_id:
				lead = lead_obj.search([('id','=',lead_id),('active','=',True)],limit=1)
				lead.product_ids = [(6,0,product.product_tmpl_id.ids)]
				return {
						'success': True,
						'status': 'Product Updated in Lead.',
						'code': 200,
						'response':lead.partner_id.id,
						'case_id': lead.case_id,
						'lead_id': lead.id,
					}
				# return _success_200("Product Updated in Lead", data)
			else:
				source_id = request.env['utm.source'].sudo().search([('name','=',"Direct"),('active','=',True)],limit=1).id
				lead_vals = {
					"name": product.name,
					"partner_id": dummy_user.id,
					"stage_id": 1,
					"product_ids": [(6,0,product.product_tmpl_id.ids)],
					"source_id": source_id,
					"phone": dummy_user.mobile
				}
				new_lead_id = lead_obj.with_context({
					'default_type': 'lead',
					'search_default_type': 'lead',
					'search_default_to_process': 1
				}).sudo().create(lead_vals)
				if new_lead_id:
					template_id = request.env.ref('oss_contact.mail_template_enquiry_crm_lead')
					email_context = request.env.context.copy()
					email_context.update({
						'email_to': new_lead_id.partner_id.email,
						'crm_enquiry_id' : new_lead_id.case_id,
						'enquiry_product': new_lead_id.product_ids.ids,
						'csp_name': new_lead_id.partner_id.name,
					})
					if template_id:
						template_id.with_context(email_context).sudo().send_mail(new_lead_id.id, True)
					return {
						'success': True,
						'status': 'New Direct Lead Created.',
						'code': 200,
						'response': dummy_user.id,
						'case_id': new_lead_id.case_id,
						'lead_id': new_lead_id.id,
					}
				else:
					return _error_400('Direct Lead not Created.')
		except Exception as e:
			return _error_400("Direct Lead Not Created." + str(e))

	@http.route('/api/lead/multi_delete', auth='none', type="json", methods=['POST'])
	def lead_multi_delete(self, **kwargs):
		data = request.jsonrequest
		lead_id = data.get('lead_id')
		if lead_id:
			lead_objs = request.env['crm.lead'].sudo().search([('id','in',lead_id),('active','=',True)])
			if not lead_objs:
				return  _error_400("Invalid Lead ID in request payload")
			try:
				for obj in lead_objs:
					obj.action_set_lost()
				not_deleted = [x for x in lead_id if x not in lead_objs._ids]
				return _success_200(str(lead_objs._ids) + " has been deleted. "  +  str(not_deleted) + " deletion failed!!", {})
			except Exception as e:
				return _error_400(str(lead_id) + "Lead Not Deleted. " + str(e))
		else:
			return  _error_400("Invalid request payload")

class APICountry(http.Controller):
	@http.route('/api/get_country', methods=["GET"], auth="none")
	def get_country(self, **kw):
		if not request.uid:
			request.uid = odoo.SUPERUSER_ID
		values = request.params.copy()
		res_country_group_obj = request.env['res.country.group'].sudo().search([('name','=','Sita_SA')],limit=1)
		res_country_obj = request.env['res.country'].sudo()
		country_ids = res_country_obj.search([])
		all_country_list = []
		base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
		for country in res_country_group_obj.country_ids:
			vals = {
				"id": country.id if country.id else '',
				"name": country.name if country.name else '',
				"code": country.code if country.code else '',
				"phone_code": country.phone_code if country.phone_code else '',
				"currency_id": country.currency_id.id if country.currency_id else '',
				"currency_name": country.currency_id.name if country.currency_id.id else '',
				"image": base64.b64encode(requests.get(base_url + country.image_url).content).decode('utf-8') if country.image_url else ''
			}
			all_country_list.append(vals)
		return Response(json.dumps(all_country_list), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")

class APICountryState(http.Controller):
	@http.route('/api/get_country_state', methods=["GET"], auth="none")
	def get_country_state(self, **kw):
		if not request.uid:
			request.uid = odoo.SUPERUSER_ID
		values = request.params.copy()
		res_country_group_obj = request.env['res.country.group'].sudo().search([('name','=','Sita_SA')],limit=1)
		res_country_state_obj = request.env['res.country.state'].sudo()
		country_state_ids = res_country_state_obj.search([('country_id','in',res_country_group_obj.country_ids.ids)])
		all_country_state_list = []
		for country_state in country_state_ids:
			vals = {
				"id": country_state.id if country_state.id else '',
				"name": country_state.name if country_state.name else '',
				"code": country_state.code if country_state.code else '',
				"country_id": country_state.country_id.id if country_state.country_id else '',
			}
			all_country_state_list.append(vals)
		return Response(json.dumps(all_country_state_list), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")

class APIIndustries(http.Controller):
	@http.route('/api/get_industries', methods=["GET"], auth="none")
	def get_industries(self, **kw):
		if not request.uid:
			request.uid = odoo.SUPERUSER_ID
		values = request.params.copy()
		res_industry_obj = request.env['res.partner.industry'].sudo()
		industry_ids = res_industry_obj.search([('active','=',True)])
		all_industry_list = []
		for industry in industry_ids:
			vals = {
				"id": industry.id if industry.id else '',
				"name": industry.name if industry.name else '',
			}
			all_industry_list.append(vals)
		return Response(json.dumps(all_industry_list), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")

class APILead(http.Controller):

	def _get_site_address(self, site_address):
		tp_links = []
		for i in site_address.tp_link_model_id:
			tp_links.append({"tp_type": i.tp_type if i.tp_type else '', "tp_bandwidth": i.tp_bandwidth if i.tp_bandwidth else '', "bandwidth_type": i.bandwidth_type if i.bandwidth_type else '', "tp_sla": i.tp_sla if i.tp_sla else '', "tp_media": i.tp_media if i.tp_media else ''})
		router_list = []

		hardware_routers1 = ''
		hardware_routers2 = ''
		if len(site_address.router_ids) >= 1:
			hardware_routers1 = site_address.router_ids[0].id
		if len(site_address.router_ids) >= 2:
			hardware_routers2 = site_address.router_ids[1].id
		return {
			"site_id": site_address.id,
			#"site_code": site_address.site_code if site_address.site_code else '',
			"name_of_site": site_address.name_of_site if site_address.name_of_site else '',
			"hosting_models": site_address.hosting_models if site_address.hosting_models else '',
			"site_type": site_address.site_type if site_address.site_type else '',
			"spoc_lname": site_address.spoc_lname if site_address.spoc_lname else '',
			"site_sla": site_address.site_sla if site_address.site_sla else '',
			"last_mile_connectivity": site_address.last_mile_connectivity if site_address.last_mile_connectivity else '',
			"existing_id": site_address.existing_id if site_address.existing_id else '',
			"existing_site_code": site_address.existing_site_code if site_address.existing_site_code else '',
			"redundancy_requirement": site_address.redundancy_requirement if site_address.redundancy_requirement else '',
			"hardware_support_level": site_address.hardware_support_level if site_address.hardware_support_level else '',
			"head_office_site_sla": site_address.head_office_site_sla if site_address.head_office_site_sla else '',
			'tp_link1': tp_links[0] if len(tp_links)>=1 else {},
			'tp_link2': tp_links[1] if len(tp_links)>=2 else {},
			"hardware_router1": hardware_routers1,
			"hardware_router2": hardware_routers2,
			"wireless_for_lan": site_address.wireless_for_lan if site_address.wireless_for_lan else '',
			"site_internet_usage": site_address.site_internet_usage if site_address.site_internet_usage else '',
			"name": site_address.name if site_address.name else '',
			"mobile": site_address.mobile if site_address.mobile else '',
			"email": site_address.email if site_address.email else '',
			'street': site_address.street if site_address.street else '',
			'street2': site_address.street2 if site_address.street2 else '',
			'zip': site_address.zip if site_address.zip else '',
			'city': site_address.city if site_address.city else '',
			'state_id': site_address.state_id.id if site_address.state_id else False,
			'country_id': site_address.country_id.id if site_address.country_id else False,
			"partner_latitude": site_address.partner_latitude if site_address.partner_latitude else '',
			"partner_longitude": site_address.partner_longitude if site_address.partner_longitude else ''
		}

	@http.route(['/api/get_new_lead_filter','/api/get_new_lead_filter/<int:lead_id>', "/api/get_new_lead_filter/<string:stage>"], type="json", methods=["POST"], auth="none")
	def get_new_lead_filter(self, lead_id=False, stage=False, **kw):
		try:
			limit = None
			offset = None
			if not request.uid:
				request.uid = odoo.SUPERUSER_ID
			domain = []
			data = request.jsonrequest
			if data.get('search_filter'):
				domain += [('case_id','ilike',data.get('search_filter'))]
			else:
				if data.get('max_page') and data.get('min_page'):
					limit = data.get('max_page') - data.get('min_page')
					offset = data.get('min_page')
				if len(data):
					values = data.get("filter_list")
					if values:
						domain += _get_filter_domain(values)
				if lead_id:
					domain += [('case_id','!=', False),('id','=',lead_id),('active','=',True)]
				else:
					domain += [('case_id','!=', False),('active','=',True)]
			if stage:
				domain += [('type','=',stage)]
			crm_lead_obj = request.env['crm.lead'].sudo()
			leads_ids = crm_lead_obj.search(domain, order='id desc', limit=limit, offset=offset)
			all_leads_list = []
			for lead in leads_ids:
				site_address_list = []
				for site_address in lead.site_address_ids:
					site_address_list.append(self._get_site_address(site_address))
				products_list = []
				cpe_model_list = []
				for product_cpe in lead.cpe_model_ids:
					cpe_model_vals = {'oem_model_id': product_cpe.oem_model_id.id if product_cpe.oem_model_id else '',
									'oem_model_name': product_cpe.oem_model_id.name if product_cpe.oem_model_id and product_cpe.oem_model_id.name else '',
									'cpe_model_name': product_cpe.product_id.name if product_cpe.product_id else '',
									'cpe_model_id': product_cpe.product_id.id if product_cpe.product_id else '',
									'no_of_devices': product_cpe.no_of_devices if product_cpe.no_of_devices else ''}
					cpe_model_list.append(cpe_model_vals)
				for product in lead.product_ids:
					product_vals = {'name': product.name, 'id': product.product_variant_ids[0].id}
					products_list.append(product_vals)
				task_list = []
				for task in lead.task_ids:
					task_vals = {'name': task.name if task.name else '', 'id': task.id, 'due_date': task.due_date.strftime('%Y-%m-%d %H:%M') if task.due_date else '',
								'assigned_to': task.assigned_to.name if task.assigned_to else '', 'assigned_by': task.assigned_by.name if task.assigned_by else '',
								'state': task.state if task.state else '', 'task_id': task.task_id if task.task_id else ''}
					task_list.append(task_vals)
				stakeholder_list = []
				for stakeholder in lead.stakeholder_ids:
					stakeholder_vals = {'name': stakeholder.name if stakeholder.name else '', 'id': stakeholder.id,
										'photo': base64.b64encode(stakeholder.photo).decode(
											'utf-8') if stakeholder.photo else False,
										'stakeholder_id': stakeholder.stakeholder_id if stakeholder.stakeholder_id else ''}
					stakeholder_list.append(stakeholder_vals)

				status_list = [{'name': lead.stage_id.name if lead.stage_id else '', 'id': lead.stage_id.id if lead.stage_id else ''}]
				source_list = [{'name': lead.source_id.name if lead.source_id else '', 'id': lead.source_id.id if lead.source_id else ''}]
				currency_list = [{'name': lead.currency_id.name if lead.currency_id else '', 'id': lead.currency_id.id if lead.currency_id else ''}]
				app_modeling_list = []
				for app_model in lead.app_modeling_ids:
					app_model_vals = {'name': app_model.name if app_model.name else '', 'application_id': app_model.id,
										'application_hosted': app_model.application_hosted if app_model.application_hosted else '',
										'ip_addr_fqdn': app_model.ip_addr_fqdn if app_model.ip_addr_fqdn else '',
										'port': app_model.port if app_model.port else '',
										'application_concurrent_users': app_model.application_concurrent_users if app_model.application_concurrent_users else '',
										'per_session_bandwith': app_model.per_session_bandwith if app_model.per_session_bandwith else '',
										'bandwidth_type': app_model.bandwidth_type if app_model.bandwidth_type else '',
										'application_qos_parameter': app_model.application_qos_parameter if app_model.application_qos_parameter else '',
										'application_priority': app_model.application_priority if app_model.application_priority else ''}
					app_modeling_list.append(app_model_vals)

				cor_sites_list = []
				for cor_id in lead.cor_ramp_ids:
					redundency_list = []
					for redundency_id in cor_id.redundency_id:
						#redundency_vals = {
						#	'name': redundency_id.name if redundency_id.name else '', 
						#	'id': redundency_id.id
						#	}
						redundency_list.append(redundency_id.name if redundency_id.name else '',)
					cor_sites_vals = {'cor_site_name': cor_id.name if cor_id.name else '', 
										'cor_id': cor_id.id,
										'provider_name': cor_id.provider_name if cor_id.provider_name else '',
										'cor_city': cor_id.cor_city if cor_id.cor_city else '',
										'cor_state': cor_id.cor_state.id if cor_id.cor_state else '',
										'cor_country': cor_id.cor_country.id if cor_id.cor_country else '',
										'cor_zip': cor_id.cor_zip if cor_id.cor_zip else '',
										'cor_country_code': cor_id.cor_country_code if cor_id.cor_country_code else '',
										'redundency_id': redundency_list,
										'site_spoc_fname': cor_id.site_spoc_fname if cor_id.site_spoc_fname else '',
										'site_spoc_lname': cor_id.site_spoc_lname if cor_id.site_spoc_lname else '',
										'site_spoc_phone': cor_id.site_spoc_phone if cor_id.site_spoc_phone else '',
										'site_spoc_email': cor_id.site_spoc_email if cor_id.site_spoc_email else '',
										'bandwidth': cor_id.bandwidth if cor_id.bandwidth else '',
										'bandwidth_type': cor_id.bandwidth_type if cor_id.bandwidth_type else '',
										'total_liscenses': cor_id.total_liscenses if cor_id.total_liscenses else '',
										'location_a_end': cor_id.location_a_end if cor_id.location_a_end else '',
										'transit_wan_edge': cor_id.transit_wan_edge if cor_id.transit_wan_edge else '',
										'total_liscenses': cor_id.total_liscenses if cor_id.total_liscenses else '',
										}
					cor_sites_list.append(cor_sites_vals)

				security_requirement_list = []
				for security_id in lead.security_requirement_ids:
					security_vals = {'name': security_id.name, 'id': security_id.id}
					security_requirement_list.append(security_vals)
				certainity_list = []
				for certainity_id in lead.certainity:
					certainity_vals = {'id': certainity_id.id, 'name': certainity_id.name}
					certainity_list.append(certainity_vals)
				partner_name = lead.partner_id.spoc_name + " " + lead.partner_id.spoc_lname if lead.partner_id and lead.partner_id.spoc_name and lead.partner_id.spoc_lname else ""
				customervals = {
					"lead_id": lead.id,
					"linked_leads": lead.linked_lead_ids.ids,
					'case_id': lead.case_id,
					'stage': "Lead" if lead.type == 'lead' else "Opportunity",
					'progress_bar': "Qualify" if lead.type == 'lead' else "Develop",
					'status': status_list,
					'source' : source_list,
					'received' : str(lead.create_date) if lead.create_date else "",
					'updated': str(lead.write_date) if lead.write_date else "",
					'name': partner_name if partner_name else "",
					'designation': lead.partner_id.designation if lead.partner_id.designation else "",
					'department': lead.partner_id.department if lead.partner_id.department else "",
					'organization_name': lead.partner_id.name if lead.partner_id.name else "",
					'organization_street': lead.partner_id.street if lead.partner_id.street else "",
					'organization_area_details': lead.partner_id.street2 if lead.partner_id.street2 else "",
					'organization_city': lead.partner_id.city if lead.partner_id.city else "",
					'organization_country_id': lead.partner_id.country_id.id if lead.partner_id.country_id else "",
					'organization_country': lead.partner_id.country_id.name if lead.partner_id.country_id else "",
					'organization_state_id': lead.partner_id.state_id.id if lead.partner_id.state_id else "",
					'organization_state': lead.partner_id.state_id.name if lead.partner_id.state_id else "",
					'postal_code': lead.partner_id.zip if lead.partner_id.zip else "",
					'registration_number': lead.partner_id.organization_registration if lead.partner_id.organization_registration else "",
					'contact_number': lead.partner_id.mobile if lead.partner_id.mobile else "",
					'email': lead.partner_id.email if lead.partner_id.email else "",
					'industry_id': lead.partner_id.industry_id.id if lead.partner_id.industry_id else "",
					'industry_name': lead.partner_id.industry_id.name if lead.partner_id.industry_id else "",
					'business_req_product': lead.business_req_product if lead.business_req_product else "",
					'product_value_business': lead.product_value_business if lead.product_value_business else "",
					'purchase_process': lead.purchase_process if lead.purchase_process else "",
					'expected_delivery_date': lead.expected_delivery_date.strftime('%d/%m/%Y') if lead.expected_delivery_date else "",
					'remarks': lead.remarks if lead.remarks else "",
					'is_spoc': lead.is_spoc if lead.is_spoc else "",
					'spoc_name': lead.spoc_name if lead.spoc_name else "",
					'spoc_email': lead.spoc_email if lead.spoc_email else "",
					'spoc_contact_number': lead.spoc_contact_number if lead.spoc_contact_number else "",
					'no_of_sites': lead.no_of_sites if lead.no_of_sites else "",
					'is_public_cloud_access': lead.is_public_cloud_access if lead.is_public_cloud_access else "",
					'public_cloud_name': lead.public_cloud_name if lead.public_cloud_name else "",
					'public_bandwidth': lead.public_bandwidth if lead.public_bandwidth else "",
					'existing_routing_protocol': lead.existing_routing_protocol if lead.existing_routing_protocol else "",
					'topology_requirement': lead.topology_requirement if lead.topology_requirement else "",
					'cpe_requirement': lead.cpe_requirement if lead.cpe_requirement else "",
					'cpe_model_ids': cpe_model_list ,
					'site_internet_usage': lead.site_internet_usage if lead.site_internet_usage else "",
					'sites_address': site_address_list ,
					'is_application_modelling': lead.is_application_modelling if lead.is_application_modelling else "",
					'no_of_applications': lead.no_of_applications if lead.no_of_applications else "",
					'lost_additional_remark': lead.lost_additional_remark if lead.lost_additional_remark else "",
					'estimated_budget': lead.estimated_budget if lead.estimated_budget else "",
					"currency": currency_list,
					'products': products_list ,
					'tasks': task_list ,
					'stakeholders': stakeholder_list,
					'cor_sites': cor_sites_list,
					'application_details': app_modeling_list,
					'security_requirement_ids': security_requirement_list,
					"certainity": certainity_list,
					"billing_cycle": lead.billing_cycle if lead.billing_cycle else '',
					"contract_duration": lead.contract_duration if lead.contract_duration else ''
				}
				all_leads_list.append(customervals)
			return _success_200('Lead Data.', {"count": len(all_leads_list), "data":all_leads_list})
		except Exception as e:
			return _error_400("Failed" + str(e))

	@http.route(['/api/get_new_lead','/api/get_new_lead/<int:lead_id>'], methods=["GET"], auth="none")
	def get_new_lead(self, lead_id=False, **kw):
		if not request.uid:
			request.uid = odoo.SUPERUSER_ID
		values = request.params.copy()
		crm_lead_obj = request.env['crm.lead'].sudo()
		if lead_id:
			leads_ids = crm_lead_obj.search([('id','=',lead_id),('case_id','!=', False),('active','=',True)])
		else:
			leads_ids = crm_lead_obj.search([('case_id','!=', False),('active','=',True)])
		all_leads_list = []
		for lead in leads_ids:
			site_address_list = []
			for site_address in lead.site_address_ids:
				site_address_list.append(self._get_site_address(site_address))
			products_list = []
			cpe_model_list = []
			for product_cpe in lead.cpe_model_ids:
				cpe_model_vals = {'oem_model_id': product_cpe.oem_model_id.id if product_cpe.oem_model_id else '',
								'oem_model_name': product_cpe.oem_model_id.name if product_cpe.oem_model_id and product_cpe.oem_model_id.name else '',
								'cpe_model_name': product_cpe.product_id.name if product_cpe.product_id else '',
								'cpe_model_id': product_cpe.product_id.id if product_cpe.product_id else '',
								'no_of_devices': product_cpe.no_of_devices if product_cpe.no_of_devices else ''}
				cpe_model_list.append(cpe_model_vals)
			for product in lead.product_ids:
				product_vals = {'name': product.name, 'id': product.product_variant_ids.id}
				products_list.append(product_vals)
			task_list = []
			for task in lead.task_ids:
				task_vals = {'name': task.name if task.name else '', 'id': task.id, 'due_date': task.due_date.strftime('%Y-%m-%d %H:%M') if task.due_date else '',
							 'assigned_to': task.assigned_to.name if task.assigned_to else '', 'assigned_by': task.assigned_by.name if task.assigned_by else '',
							 'state': task.state if task.state else '', 'task_id': task.task_id if task.task_id else ''}
				task_list.append(task_vals)
			stakeholder_list = []
			for stakeholder in lead.stakeholder_ids:
				stakeholder_vals = {'name': stakeholder.name if stakeholder.name else '', 'id': stakeholder.id,
									'photo': base64.b64encode(stakeholder.photo).decode(
										'utf-8') if stakeholder.photo else False,
									'stakeholder_id': stakeholder.stakeholder_id if stakeholder.stakeholder_id else ''}
				stakeholder_list.append(stakeholder_vals)

			status_list = [{'name': lead.stage_id.name if lead.stage_id else '', 'id': lead.stage_id.id if lead.stage_id else ''}]
			source_list = [{'name': lead.source_id.name if lead.source_id else '', 'id': lead.source_id.id if lead.source_id else ''}]
			currency_list = [{'name': lead.currency_id.name if lead.currency_id else '', 'id': lead.currency_id.id if lead.currency_id else ''}]
			app_modeling_list = []
			for app_model in lead.app_modeling_ids:
				app_model_vals = {'name': app_model.name if app_model.name else '', 'application_id': app_model.id,
									'application_hosted': app_model.application_hosted if app_model.application_hosted else '',
									'ip_addr_fqdn': app_model.ip_addr_fqdn if app_model.ip_addr_fqdn else '',
									'port': app_model.port if app_model.port else '',
									'application_concurrent_users': app_model.application_concurrent_users if app_model.application_concurrent_users else '',
									'per_session_bandwith': app_model.per_session_bandwith if app_model.per_session_bandwith else '',
									'bandwidth_type': app_model.bandwidth_type if app_model.bandwidth_type else '',
									'application_qos_parameter': app_model.application_qos_parameter if app_model.application_qos_parameter else '',
									'application_priority': app_model.application_priority if app_model.application_priority else ''}
				app_modeling_list.append(app_model_vals)

			cor_sites_list = []
			for cor_id in lead.cor_ramp_ids:
				redundency_list = []
				for redundency_id in cor_id.redundency_id:
					#redundency_vals = {
					#	'name': redundency_id.name if redundency_id.name else '', 
					#	'id': redundency_id.id
					#	}
					redundency_list.append(redundency_id.name if redundency_id.name else '',)
				cor_sites_vals = {'cor_site_name': cor_id.name if cor_id.name else '', 
									'cor_id': cor_id.id,
									'provider_name': cor_id.provider_name if cor_id.provider_name else '',
									'cor_city': cor_id.cor_city if cor_id.cor_city else '',
									'cor_state': cor_id.cor_state.id if cor_id.cor_state else '',
									'cor_country': cor_id.cor_country.id if cor_id.cor_country else '',
									'cor_zip': cor_id.cor_zip if cor_id.cor_zip else '',
									'cor_country_code': cor_id.cor_country_code if cor_id.cor_country_code else '',
									'redundency_id': redundency_list,
									'site_spoc_fname': cor_id.site_spoc_fname if cor_id.site_spoc_fname else '',
									'site_spoc_lname': cor_id.site_spoc_lname if cor_id.site_spoc_lname else '',
									'site_spoc_phone': cor_id.site_spoc_phone if cor_id.site_spoc_phone else '',
									'site_spoc_email': cor_id.site_spoc_email if cor_id.site_spoc_email else '',
									'bandwidth': cor_id.bandwidth if cor_id.bandwidth else '',
									'bandwidth_type': cor_id.bandwidth_type if cor_id.bandwidth_type else '',
									'total_liscenses': cor_id.total_liscenses if cor_id.total_liscenses else '',
									'location_a_end': cor_id.location_a_end if cor_id.location_a_end else '',
									'transit_wan_edge': cor_id.transit_wan_edge if cor_id.transit_wan_edge else '',
									'total_liscenses': cor_id.total_liscenses if cor_id.total_liscenses else '',
									}
				cor_sites_list.append(cor_sites_vals)

			security_requirement_list = []
			for security_id in lead.security_requirement_ids:
				security_vals = {'name': security_id.name, 'id': security_id.id}
				security_requirement_list.append(security_vals)

			certainity_list = []
			for certainity_id in lead.certainity:
				certainity_vals = {'id': certainity_id.id, 'name': certainity_id.name}
				certainity_list.append(certainity_vals)
			partner_name = lead.partner_id.spoc_name + " " + lead.partner_id.spoc_lname if lead.partner_id and lead.partner_id.spoc_name and lead.partner_id.spoc_lname else ""
			customervals = {
				"lead_id": lead.id,
				"linked_leads": lead.linked_lead_ids.ids,
				'case_id': lead.case_id,
				'stage': "Lead" if lead.type == 'lead' else "Opportunity",
				'progress_bar': "Qualify" if lead.type == 'lead' else "Develop",
				'status': status_list,
				'source' : source_list,
				'received' : str(lead.create_date) if lead.create_date else "",
				'updated': str(lead.write_date) if lead.write_date else "",
				'name': partner_name if partner_name else "",
				'designation': lead.partner_id.designation if lead.partner_id.designation else "",
				'department': lead.partner_id.department if lead.partner_id.department else "",
				'organization_name': lead.partner_id.name if lead.partner_id.name else "",
				'organization_street': lead.partner_id.street if lead.partner_id.street else "",
				'organization_area_details': lead.partner_id.street2 if lead.partner_id.street2 else "",
				'organization_city': lead.partner_id.city if lead.partner_id.city else "",
				'organization_country_id': lead.partner_id.country_id.id if lead.partner_id.country_id else "",
				'organization_country': lead.partner_id.country_id.name if lead.partner_id.country_id else "",
				'organization_state_id': lead.partner_id.state_id.id if lead.partner_id.state_id else "",
				'organization_state': lead.partner_id.state_id.name if lead.partner_id.state_id else "",
				'postal_code': lead.partner_id.zip if lead.partner_id.zip else "",
				'registration_number': lead.partner_id.organization_registration if lead.partner_id.organization_registration else "",
				'contact_number': lead.partner_id.mobile if lead.partner_id.mobile else "",
				'email': lead.partner_id.email if lead.partner_id.email else "",
				'industry_id': lead.partner_id.industry_id.id if lead.partner_id.industry_id else "",
				'industry_name': lead.partner_id.industry_id.name if lead.partner_id.industry_id else "",
				'business_req_product': lead.business_req_product if lead.business_req_product else "",
				'product_value_business': lead.product_value_business if lead.product_value_business else "",
				'purchase_process': lead.purchase_process if lead.purchase_process else "",
				'expected_delivery_date': lead.expected_delivery_date.strftime('%d/%m/%Y') if lead.expected_delivery_date else "",
				'remarks': lead.remarks if lead.remarks else "",
				'is_spoc': lead.is_spoc if lead.is_spoc else "",
				'spoc_name': lead.spoc_name if lead.spoc_name else "",
				'spoc_email': lead.spoc_email if lead.spoc_email else "",
				'spoc_contact_number': lead.spoc_contact_number if lead.spoc_contact_number else "",
				'no_of_sites': lead.no_of_sites if lead.no_of_sites else "",
				'is_public_cloud_access': lead.is_public_cloud_access if lead.is_public_cloud_access else "",
				'public_cloud_name': lead.public_cloud_name if lead.public_cloud_name else "",
				'public_bandwidth': lead.public_bandwidth if lead.public_bandwidth else "",
				'existing_routing_protocol': lead.existing_routing_protocol if lead.existing_routing_protocol else "",
				'topology_requirement': lead.topology_requirement if lead.topology_requirement else "",
				'cpe_requirement': lead.cpe_requirement if lead.cpe_requirement else "",
				'cpe_model_ids': cpe_model_list ,
				'site_internet_usage': lead.site_internet_usage if lead.site_internet_usage else "",
				# 'url_filtering': lead.url_filtering if lead.url_filtering else "",
				# 'intrusion_prevention_system': lead.intrusion_prevention_system if lead.intrusion_prevention_system else "",
				# 'local_attack_defence': lead.local_attack_defence if lead.local_attack_defence else "",
				# 'malware_protection': lead.malware_protection if lead.malware_protection else "",
				'sites_address': site_address_list ,
				'is_application_modelling': lead.is_application_modelling if lead.is_application_modelling else "",
				'no_of_applications': lead.no_of_applications if lead.no_of_applications else "",
				'lost_additional_remark': lead.lost_additional_remark if lead.lost_additional_remark else "",
				'estimated_budget': lead.estimated_budget if lead.estimated_budget else "",
				"currency": currency_list,
				'products': products_list ,
				'tasks': task_list ,
				'stakeholders': stakeholder_list,
				'cor_sites': cor_sites_list,
				'application_details': app_modeling_list,
				'security_requirement_ids': security_requirement_list,
				"certainity": certainity_list,
				"billing_cycle": lead.billing_cycle if lead.billing_cycle else '',
				"contract_duration": lead.contract_duration if lead.contract_duration else '',
				"total_yrc": lead.total_rc if lead.total_rc else '',
				"total_nrc": lead.total_nrc if lead.total_nrc else '',
				"total_mrc": lead.total_mrc if lead.total_mrc else '',
			}
			all_leads_list.append(customervals)
		return Response(json.dumps(all_leads_list), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")

	@http.route('/api/update_lead', type="json", methods=["POST"], auth="none")
	def update_lead(self, **kw):
		vals = {}
		data = request.jsonrequest
		lead_id = data.get('lead_id')
		try:
			lead = request.env['crm.lead'].sudo().search([('id','=',lead_id),('active','=',True)],limit=1)
			if not lead:
				return _error_400("Lead Id Not Found")	
			if data.get("purchase_process") and data.get("purchase_process") not in dict(request.env['crm.lead'].sudo()._fields["purchase_process"].selection).keys():
				return  _error_400("Invalid 'Purchase Process' in request payload")
			product_id = request.env['product.product'].sudo().search([('id','in',data.get('products')),('active','=',True)])
			if data.get('product_ids') and not product_id:
				return  _error_400("Product Not Found")
			# source_id = request.env['utm.source'].sudo().browse(data.get('source')).exists()
			# if data.get('source_id') and not source_id:
			# 	return  _error_400("Source Not Found")
			currency_id = request.env['res.currency'].sudo().browse(data.get('currency')).exists()
			if data.get('currency_id') and not currency_id:
				return  _error_400("Currency Not Found")
			if data.get('expected_delivery_date'):
				try:
					convert_delivery_date = datetime.strptime(data.get('expected_delivery_date'), '%d/%m/%Y').strftime('%Y-%m-%d')
				except:
					return  _error_400("Does not match format expected_delivery_date %d/%m/%Y")
			try:
				vals = {
						# ""source_id": source_id.id,
						"product_ids": [(6,0,product_id.product_tmpl_id.ids)],
						"expected_delivery_date": convert_delivery_date,
						"estimated_budget": data.get('estimated_budget'),
						"currency_id": currency_id.id,
						"purchase_process": data.get('purchase_process'),
						# "product_package": '',
						"billing_cycle": data.get('billing_cycle') if data.get('billing_cycle') else False,
						"contract_duration": data.get('contract_duration') if data.get('contract_duration') else False,
						"certainity": data.get("certainity")
						# "existing_account": "",
						# "existing_contact" : "",
					}
				lead.sudo().write(vals)
				return _success_200('Lead Updated.', data)
			except Exception as e:
				return _error_400("Lead Not Updated." + str(e))
		except Exception as e:
			return  _error_400("Invalid request payload. " + str(e))


class SummaryDetails(http.Controller):
	@http.route('/api/summary_details_update', auth='none', type="json", methods=['POST'])
	def summay_details_json(self, **kwargs):
		vals = {}
		data = request.jsonrequest
		lead_id = data.get('id')
		selection_list = ['product_value_business']
		for sl in selection_list:
			if data.get(sl) and data.get(sl) not in dict(request.env['crm.lead'].sudo()._fields[sl].selection).keys():
				return  _error_400("Invalid request payload")
		if lead_id:
			try:
				lead_obj = request.env['crm.lead'].sudo().search([('id','=',int(lead_id)),('active','=',True)])
				if not lead_obj:
					return _error_400("lead Id Not Found")
				vals['business_req_product'] = data.get('business_req_product')
				vals['product_value_business'] = data.get('product_value_business')
				vals['expected_delivery_date'] = data.get('expected_delivery_date')
				vals['remarks'] = data.get('remarks')
				vals['is_spoc'] = True if data.get('is_spoc') == 'True' else False
				vals['spoc_name'] = data.get('spoc_name')
				vals['spoc_email'] = data.get('spoc_email')
				vals['spoc_contact_number'] = data.get('spoc_contact_number')
				if lead_obj:
					lead_obj.with_context(is_api=True).write(vals)
					return _success_200('Data updated.', data)
			except Exception as e:
				return _error_400("Data Not Updated." + str(e))
		else:
			return _error_400("lead Id Not Found")

class GeneralDetails(http.Controller):
	@http.route('/api/general_details_update', auth='none', type="json", methods=['POST'])
	def general_details_json(self, **kwargs):
		vals = {}
		data = request.jsonrequest
		lead_id = data.get('id')
		product_obj = request.env['product.product'].sudo()
		selection_list = ['topology_requirement', 'public_cloud_name',"cpe_requirement", "existing_routing_protocol", "site_internet_usage"]
		for sl in selection_list:
			if data.get(sl) and data.get(sl) not in dict(request.env['crm.lead'].sudo()._fields[sl].selection).keys():
				return _error_400("Invalid request payload")
		if lead_id:
			lead_obj = request.env['crm.lead'].sudo().search([('id','=',int(lead_id)),('active','=',True)],limit=1)
			if not lead_obj:
				return _error_400("lead Id Not Found")
			else:
				try:
					model_line_ids = []
					for model_id in data.get('cpe_model_ids'):
						product_id = product_obj.search([('id','=',model_id[0].get('product_id')),('active','=',True)],limit=1)
						if not product_id:
							return _error_400("product id Not Found")
						line_dict = {
							'no_of_devices': model_id[0].get('no_of_devices'),
							'product_id': model_id[0].get('product_id'),
						}
						model_line_ids.append([0,0,line_dict])
					update_vals = {
						'no_of_sites': data.get('no_of_sites'),
						'topology_requirement': data.get('topology_requirement'),
						'is_public_cloud_access': True if data.get('is_public_cloud_access') == 'true' else False,
						'public_cloud_name':  data.get('public_cloud_name'),
						'public_bandwidth': data.get('public_bandwidth'),
						'cpe_requirement': data.get('cpe_requirement'),
						'existing_routing_protocol': data.get('existing_routing_protocol'),
						'site_internet_usage': data.get('site_internet_usage'),
						'description': data.get('description'),
						'cpe_model_ids': model_line_ids
						}
					lead_obj.write(update_vals)
					return _success_200('Data updated.', data)
				except Exception as e:
					return _error_400("Data Not Updated." + str(e))
		else:
			return _error_400("lead Id Not Found")

class SiteDetails(http.Controller):
	def _validate_selection_vals(self, data):
		partner_obj = request.env['res.partner'].sudo()
		selection_list = ['last_mile_connectivity','wireless_for_lan', 'redundancy_requirement']
		if any(data.get(i) and data.get(i) not in list(dict(partner_obj._fields[i].selection).keys()) for i in selection_list):
			return False
		for tp in ['tp_link1', 'tp_link2']:
			if data.get(tp):
				if any(data.get(tp).get(i) and data.get(tp).get(i) not in list(dict(request.env['transport.links'].sudo()._fields[i].selection).keys()) for i in ['tp_type', 'tp_media']):
					return False
		if data.get('last_mile_connectivity') == 'yes':
			if not data.get("existing_id") or not data.get("existing_site_code"):
				return False
		return True

	@http.route('/api/site_details/create', auth='public', type="json", methods=['POST'])
	def site_details_create(self, **kwargs):
		data = request.jsonrequest
		lead_id = data.get('lead_id')
		res = self._validate_selection_vals(data)
		partner_obj = request.env['res.partner'].sudo()
		if lead_id and res:
			lead_obj = request.env['crm.lead'].sudo().search([('id','=',lead_id),('active','=',True)],limit=1)
			if not lead_obj:
				return  _error_400("Lead ID does not exist!!")
			else:
				check_site = partner_obj.sudo().search([
						('name_of_site', '=ilike', data.get('name_of_site')),
						('partner_site_id', '=', lead_obj.id),('active','=',True)
					])
				if check_site:
					return  _error_403("Site Name already exists, please add unique name.")
				try:
					tp1 = request.env["transport.links"].sudo().create(data.get('tp_link1')).id if data.get('tp_link1') and len(data.get('tp_link1'))>0 else False
					tp2 = request.env["transport.links"].sudo().create(data.get('tp_link2')).id if data.get('tp_link2') and len(data.get('tp_link2'))>0 else False
					hardware_router1 = request.env["product.product"].sudo().search([('id','=',data.get('hardware_router1')),('active','=',True)],limit=1).id if data.get('hardware_router1') else False
					hardware_router2 = request.env["product.product"].sudo().search([('id','=',data.get('hardware_router2')),('active','=',True)],limit=1).id if data.get('hardware_router2') else False
					state_id = request.env['res.country.state'].sudo().search([('id','=',data.get('state_id'))],limit=1) if data.get('state_id') else False
					country_id = request.env['res.country'].sudo().search([('id','=',data.get('country_id'))],limit=1) if data.get('country_id') else False
					vals = {
						"partner_site_id": lead_obj.id,
						"name_of_site": data.get('name_of_site'),
						"hosting_models": data.get('hosting_models'),
						"site_type": data.get('site_type'),
						"name": data.get('spoc_name'),
						"spoc_lname": data.get('spoc_lname'),
						"site_sla": data.get('site_sla'),
						"last_mile_connectivity": data.get('last_mile_connectivity'),
						"existing_id": data.get('existing_id'),
						"existing_site_code": data.get('existing_site_code'),
						"redundancy_requirement": data.get("redundancy_requirement"),
						"hardware_support_level": data.get('hardware_support_level'),
						"head_office_site_sla": data.get('head_office_site_sla'),
						"is_site": True,
						"is_company": True,
						"tp_link_model_id": [(6,0,[tp1,tp2])] if tp1 or tp2 else False,
						"router_ids": [(6, 0, [hardware_router1,hardware_router2])] if hardware_router1 or hardware_router2 else False,
						"wireless_for_lan": data.get('wireless_for_lan'),
						"site_internet_usage": data.get('site_internet_usage'),
						"type": data.get('type'),
						"mobile": data.get('mobile'),
						"email": data.get('email'),
						'street': data.get('street'),
						'street2': data.get('street2'),
						'zip': data.get('zip'),
						'city': data.get('city'),
						'state_id': state_id.id,
						'country_id': country_id.id,
						"partner_latitude": data.get("partner_latitude"),
						"partner_longitude": data.get("partner_longitude"),
						"organisation_id": lead_obj.partner_id.id
					}
					site_obj = request.env['res.partner'].sudo().create(vals)
					data.update({'site_id': site_obj.id})
					return _success_200('New Site Created.', data)
				except Exception as e:
					return  _error_400("Site Not Created. " + str(e))
		else:
			return  _error_400("Invalid request payload")

	@http.route('/api/site_details/update', auth='public', type="json", methods=['POST'])
	def site_details_update(self, **kwargs):
		data = request.jsonrequest
		lead_id = data.get('lead_id')
		site_id = data.get('site_id')
		res = self._validate_selection_vals(data)
		partner_obj = request.env['res.partner'].sudo()
		if lead_id and site_id and res:
			lead_obj = request.env['crm.lead'].sudo().search([('id','=',lead_id),('active','=',True)],limit=1)
			if not lead_obj:
				return  _error_400("Lead ID does not exist!!")
			else:
				if site_id in lead_obj.site_address_ids.ids:
					try:
						tp1 = request.env["transport.links"].sudo().create(data.get('tp_link1')).id if data.get('tp_link1') and len(data.get('tp_link1'))>0 else False
						tp2 = request.env["transport.links"].sudo().create(data.get('tp_link2')).id if data.get('tp_link2') and len(data.get('tp_link2'))>0 else False
						hardware_router1 = request.env["product.product"].sudo().search([('id','=',data.get('hardware_router1')),('active','=',True)],limit=1).id if data.get('hardware_router1') else False
						hardware_router2 = request.env["product.product"].sudo().search([('id','=',data.get('hardware_router2')),('active','=',True)],limit=1).id if data.get('hardware_router2') else False
						state_id = request.env['res.country.state'].sudo().search([('id','=',data.get('state_id'))],limit=1) if data.get('state_id') else False
						country_id = request.env['res.country'].sudo().search([('id','=',data.get('country_id'))],limit=1) if data.get('country_id') else False
						site_obj = request.env['res.partner'].sudo().search([('partner_site_id','=',lead_obj.id),('id','=',site_id),('active','=',True)],limit=1)
						if not site_obj:
							return  _error_400("Site ID Not Found!!")
						update_vals = {
							"partner_site_id": lead_obj.id,
							"name_of_site": data.get('name_of_site'),
							"hosting_models": data.get('hosting_models'),
							"site_type": data.get('site_type'),
							"spoc_lname": data.get('spoc_lname'),
							"site_sla": data.get('site_sla'),
							"last_mile_connectivity": data.get('last_mile_connectivity'),
							"existing_id": data.get('existing_id'),
							"existing_site_code": data.get('existing_site_code'),
							"redundancy_requirement": data.get("redundancy_requirement"),
							"hardware_support_level": data.get('hardware_support_level'),
							"head_office_site_sla": data.get('head_office_site_sla'),
							"is_site": True,
							"is_company": True,
							"tp_link_model_id": [(6,0,[tp1, tp2])] if tp1 or tp2 else False,
							"router_ids": [(6, 0, [hardware_router1,hardware_router2])] if hardware_router1 or hardware_router2 else False,
							"wireless_for_lan": data.get('wireless_for_lan'),
							"site_internet_usage": data.get('site_internet_usage'),
							"name": data.get('name'),
							"mobile": data.get('mobile'),
							"email": data.get('email'),
							'street': data.get('street'),
							'street2': data.get('street2'),
							'zip': data.get('zip'),
							'city': data.get('city'),
							'state_id': state_id.id,
							'country_id': country_id.id,
							"partner_latitude": data.get("partner_latitude"),
							"partner_longitude": data.get("partner_longitude"),
							"organisation_id": lead_obj.partner_id.id
						}
						site_obj.sudo().write(update_vals)
						data.update({'site_id': site_obj.id})
						return _success_200('Site Data updated.', data)
					except Exception as e:
						return  _error_400("Site not updated!! " + str(e))
				else:
					return  _error_400("Invalid Site in request payload")
		else:
			return  _error_400("Invalid request payload")

	@http.route('/api/site_details/delete', auth='none', type="json", methods=['POST'])
	def site_details_delete(self, **kwargs):
		data = request.jsonrequest
		lead_id = data.get('lead_id')
		site_id = data.get('site_id')
		vals = {}
		if lead_id and site_id:
			lead_obj = request.env['crm.lead'].sudo().search([('id','=',lead_id),('active','=',True)],limit=1)
			if not lead_obj:
				return  _error_400("Lead ID not found!!")
			if site_id in lead_obj.site_address_ids.ids:
				site_obj = request.env['res.partner'].sudo().search([('id','=',site_id),('active','=',True)],limit=1)
				if not site_obj:
					return  _error_400("Invalid Site ID in request payload")
				else:
					try:
						vals = {"site_id": site_obj.id}
						site_obj.unlink()
						return _success_200('Site deleted.',vals)
					except:
						return  _error_400("Site Not Deleted.")
			else:
				return  _error_400("Invalid Site in request payload")
		else:
			return  _error_400("Invalid request payload")

	@http.route('/api/site_details/multi_delete', auth='none', type="json", methods=['POST'])
	def site_details_multi_delete(self, **kwargs):
		data = request.jsonrequest
		lead_id = data.get('lead_id')
		site_id = data.get('site_id')
		vals = {}
		if lead_id and site_id:
			lead_obj = request.env['crm.lead'].sudo().search([('id','=',lead_id),('active','=',True)],limit=1)
			if not lead_obj:
				return  _error_400("Lead ID not found!!")
			active_sites = request.env['res.partner'].sudo().search([('partner_site_id','=',lead_obj.id),('id','in',site_id),('active','=',True)])
			if not active_sites:
				return  _error_400("Invalid Site in request payload")
			try:
				active_sites.sudo().write({'active': False})
				not_deleted = [x for x in site_id if x not in active_sites.ids]
				return _success_200('Site deleted.',str(active_sites.ids) + " has been deleted. "  +  str(not_deleted) + " deletion failed!!")
			except:
				return _error_400(str(site_id) + " Site Not Deleted.")			
		else:
			return  _error_400("Invalid request payload")
	
	@http.route('/api/site_details/csv_upload', auth='none', csrf=False,  methods=['POST'])
	def site_csv_upload(self, **args):
		lead_id = args.get('lead_id')
		csv_file = args.get('csv_file')
		if lead_id and csv_file:
			lead_obj = request.env['crm.lead'].sudo().search([('id','=',int(lead_id)),('active','=',True)],limit=1)
			if not lead_obj:
				return Response(json.dumps("Lead ID not found"), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")
			file_extension = csv_file.filename.split('.')[-1]
			if file_extension not in ['xls','xlsx']:
				return Response(json.dumps("Only CSV and XLS or XLSX File extension allowed"), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")
			else:	
				cf = csv_file.read()
				lead_obj.file_name = csv_file.filename
				lead_obj.import_sites_csv = cf
				rows = lead_obj._read_xls(cf)[1]
				header_list = rows[0]
				csv_data = rows[1:]
				res = lead_obj.upload_csv_file(header_list, csv_data)
				if res.get('status'):
					return Response(json.dumps({'success': {'count':len(res.get('success')), 'data':res.get('success')}, \
						"fail": {'count':len(res.get('fail')), 'header': header_list, 'data':res.get('fail')}}), \
						status = 200, \
						headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'}, \
						content_type = "application/json")
				else:
					return Response(json.dumps("File Not Uploaded! " + res.get('result')), status = 400,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")
		else:
			return Response(json.dumps("Invalid request payload"), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")

class CloudonRamDetails(http.Controller):
	@http.route('/api/cor_create', auth='none', type='json', methods=['POST'], csrf=False)
	def cor_create(self, **kwargs):
		vals = {}
		data = request.jsonrequest
		lead_id = data.get('lead_id')
		redundency_ids = request.env['cloud.ramp.redundency'].sudo().search([('name','in',data.get('redundency_id')),('active','=',True)]) if data.get('redundency_id') else False
		if lead_id:
			lead_obj = request.env['crm.lead'].sudo().search([('id','=',int(lead_id)),('active','=',True)],limit=1)
			if not lead_obj:
				return  _error_400("lead Id Not Found")
			else:
				check_cor_site = request.env['cloud.ramp'].sudo().search([
						('name', '=ilike', data.get('cor_site_name')),
						('lead_id', '=', lead_obj.id), ('active','=',True)
					])
				if check_cor_site:
					return  _error_403("CoR Site Name already exists, please add unique name.")
				try:
					vals = {
						'lead_id': lead_obj.id,
						'name': data.get('cor_site_name'),
						'provider_name': data.get('provider_name'),
						'transit_wan_edge' : data.get('transit_wan_edge'),
						'cor_city': data.get('cor_city'),
						'cor_state': data.get('cor_state'),
						'cor_zip' : data.get('cor_zip'),
						'cor_country_code': data.get('cor_country_code'),
						'cor_country': data.get('cor_country'),
						'redundency_id': redundency_ids,
						'total_liscenses': data.get('total_liscenses'),
						'site_spoc_fname': data.get('site_spoc_fname'),
						'site_spoc_lname': data.get('site_spoc_lname'),
						'site_spoc_phone': data.get('site_spoc_phone'),
						'site_spoc_email': data.get('site_spoc_email'),
						'bandwidth': data.get('bandwidth'),
						'bandwidth_type': data.get('bandwidth_type'),
						'location_a_end': data.get('location_a_end')
					}
					cor_obj = request.env['cloud.ramp'].sudo().create(vals)
					if cor_obj:
						data.update({'cor_id':cor_obj.id})
						return _success_200("Cloud On Ramp Created.", data)
					else:
						return  _error_400("Cloud On Ramp Not Created")
				except Exception as e:
					return  _error_400("Cloud On Ramp Not Update")
		else:
			return  _error_400("Invalid request payload")

	@http.route('/api/cor_update', auth='none', type='json', methods=['POST'], csrf=False)
	def cor_update(self, **kwargs):
		vals = {}
		data = request.jsonrequest
		lead_id = data.get('lead_id')
		cor_id = data.get('cor_id')
		redundency_ids = request.env['cloud.ramp.redundency'].sudo().search([('name','in',data.get('redundency_id')),('active','=',True)]) if data.get('redundency_id') else False
		if lead_id and cor_id:
			lead_obj = request.env['crm.lead'].sudo().search([('id','=',int(lead_id)),('active','=',True)],limit=1)
			if not lead_obj:
				return  _error_400("lead Id Not Found")
			cor_obj = request.env['cloud.ramp'].sudo().search([('lead_id','=',lead_obj.id),('id','=',cor_id),('active','=',True)],limit=1)
			if not cor_obj:
				return  _error_400("Invalid cor_id in request payload")
			try:
				update_vals = {
					'lead_id': lead_obj.id,
					'name': data.get('cor_site_name'),
					'provider_name': data.get('provider_name'),
					'transit_wan_edge' : data.get('transit_wan_edge'),
					'cor_state': data.get('cor_state'),
					'cor_city': data.get('cor_city'),
					'cor_zip': data.get('cor_zip'),
					'cor_country_code': data.get('cor_country_code'),
					'cor_country': data.get('cor_country'),
					'redundency_id': redundency_ids,
					'total_liscenses': data.get('total_liscenses'),
					'site_spoc_fname': data.get('site_spoc_fname'),
					'site_spoc_lname': data.get('site_spoc_lname'),
					'site_spoc_phone': data.get('site_spoc_phone'),
					'site_spoc_email': data.get('site_spoc_email'),
					'bandwidth': data.get('bandwidth'),
					'bandwidth_type': data.get('bandwidth_type'),
					'location_a_end': data.get('location_a_end')
				}
				cor_obj.sudo().write(update_vals)
				if cor_obj:
					data.update({'cor_id':cor_obj.id})
					return _success_200("Cloud On Ramp Update.", data)
				else:
					return  _error_400("Cloud On Ramp Not Update")
			except Exception as e:
				return  _error_400("Cloud On Ramp Not Update")
		else:
			return  _error_400("Invalid request payload")

	@http.route('/api/cor_delete', auth='none', type='json', methods=['POST'], csrf=False)
	def cor_delete(self, **kwargs):
		vals = {}
		data = request.jsonrequest
		lead_id = data.get('lead_id')
		cor_id = data.get('cor_id')
		if lead_id and cor_id:
			lead_obj = request.env['crm.lead'].sudo().search([('id','=',int(lead_id)),('active','=',True)],limit=1)
			if not lead_obj:
				return  _error_400("lead Id Not Found")
			if any(x == cor_id for x in lead_obj.cor_ramp_ids.ids):
				cor_obj = request.env['cloud.ramp'].sudo().search([('id','=',data.get('cor_id')),('active','=',True)],limit=1)
				vals = {"cor_id": cor_obj.id}
				try:
					cor_obj.unlink()
					return _success_200('Cloud on Ramp deleted.', vals)
				except:
					return  _error_400("Cloud on Ramp Not Deleted.")
			else:
				return  _error_400("Invalid cor_id in request payload")
		else:
			return  _error_400("Invalid request payload")

	@http.route('/api/cor_multi_delete', auth='none', type='json', methods=['POST'], csrf=False)
	def cor_multi_delete(self, **kwargs):
		vals = {}
		data = request.jsonrequest
		lead_id = data.get('lead_id')
		cor_id = data.get('cor_id')
		if lead_id and cor_id:
			lead_obj = request.env['crm.lead'].sudo().search([('id','=',int(lead_id)),('active','=',True)],limit=1)
			if not lead_obj:
				return  _error_400("lead Id Not Found")
			active_cors = request.env['cloud.ramp'].sudo().search([('lead_id','=',lead_obj.id),('id','in',cor_id),('active','=',True)])
			if not active_cors:
				return  _error_400("Invalid cor_id in request payload")
			try:
				active_cors.sudo().write({'active': False})
				not_deleted = [x for x in cor_id if x not in active_cors.ids]
				return _success_200('Cloud on Ramp deleted.',str(active_cors.ids) + " has been deleted. "  +  str(not_deleted) + " deletion failed!!")
			except:
				return _error_400(str(cor_id) + " Cloud on Ramp Not Deleted.")
		else:
			return  _error_400("Invalid request payload")

class ApplicationDetails(http.Controller):
	@http.route('/api/application_details/create', auth='none', type='json', methods=['POST'], csrf=False)
	def application_details_create(self, **kwargs):
		vals = {}
		data = request.jsonrequest
		lead_id = data.get('lead_id')
		selection_list = ['application_hosted', 'application_priority',"application_qos_parameter", 'bandwidth_type']
		for sl in selection_list:
			if data.get(sl) and data.get(sl) not in dict(request.env['app.modeling'].sudo()._fields[sl].selection).keys():
				return  _error_400("Invalid request payload")
		if lead_id:
			lead_obj = request.env['crm.lead'].sudo().search([('id','=',lead_id),('active','=',True)],limit=1)
			if not lead_obj:
				return  _error_400("lead Id Not Found")
			try:
				check_app = request.env['app.modeling'].sudo().search([
						('name', '=ilike', data.get('name')),
						('lead_id', '=', lead_obj.id), ('active','=',True)
					])
				if check_app:
					return _error_403("Application Name already exists, please add unique name.")
				vals = {
						'lead_id': lead_obj.id,
						'port': data.get('port'),
						'name': data.get('name'),
						'application_hosted': data.get('application_hosted'),
						'ip_addr_fqdn': data.get('ip_addr_fqdn'),
						'application_concurrent_users': data.get('application_concurrent_users'),
						'per_session_bandwith': data.get('per_session_bandwith'),
						'bandwidth_type': data.get('bandwidth_type'),
						'application_qos_parameter': data.get('application_qos_parameter'),
						'application_priority': data.get('application_priority')
					}
				app_obj = request.env['app.modeling'].sudo().create(vals)
				if app_obj:
					vals.update({'application_id':app_obj.id})
					return _success_200("New Application Created.", vals)
				else:
					return  _error_400("Application Not Created")
			except Exception as e:
				return  _error_400("Application Not Created" + str(e))
		else:
			return  _error_400("Invalid request payload")

	@http.route('/api/application_details/update', auth='none', type='json', methods=['POST'], csrf=False)
	def application_details_update(self, **kwargs):
		vals = {}
		data = request.jsonrequest
		lead_id = data.get('lead_id')
		app_id = data.get('application_id')
		selection_list = ['application_hosted', 'application_priority',"application_qos_parameter", 'bandwidth_type']
		for sl in selection_list:
			if data.get(sl) and data.get(sl) not in dict(request.env['app.modeling'].sudo()._fields[sl].selection).keys():
				return  _error_400("Invalid request payload")
		if lead_id and app_id:
			lead_obj = request.env['crm.lead'].sudo().search([('id','=',lead_id),('active','=',True)],limit=1)
			if not lead_obj:
				return  _error_400("lead Id Not Found")
			app_obj = request.env['app.modeling'].sudo().search([('lead_id','=',lead_obj.id),('id','=',app_id),('active','=',True)])
			if not app_obj:
				return  _error_400("Invalid Application in request payload")
			try:
				update_vals = {
						'port': data.get('port'),
						'lead_id': lead_obj.id,
						'name': data.get('name'),
						'application_hosted': data.get('application_hosted'),
						'ip_addr_fqdn': data.get('ip_addr_fqdn'),
						'application_concurrent_users': data.get('application_concurrent_users'),
						'per_session_bandwith': data.get('per_session_bandwith'),
						'bandwidth_type': data.get('bandwidth_type'),
						'application_qos_parameter': data.get('application_qos_parameter'),
						'application_priority': data.get('application_priority')
					}
				app_obj.write(update_vals)
				if app_obj:
					vals.update({'application_id':app_obj.id})
					return _success_200("Application Update.", vals)
				else:
					return  _error_400("Application Not Update")
			except Exception as e:
				return  _error_400("Application Not Update" + str(e))
		else:
			return  _error_400("Invalid request payload")

	@http.route('/api/application_details/delete', auth='none', type="json", methods=['POST'])
	def application_details_delete(self, **kwargs):
		data = request.jsonrequest
		lead_id = data.get('lead_id')
		app_id = data.get('application_id')
		vals = {}
		if lead_id and app_id:
			lead_obj = request.env['crm.lead'].sudo().search([('id','=',lead_id),('active','=',True)],limit=1)
			if not lead_obj:
				return  _error_400("Lead ID not found!!")
			if app_id in lead_obj.app_modeling_ids.ids:
				app_obj = request.env['app.modeling'].sudo().search([('id','=',app_id),('active','=',True)],limit=1)
				if not app_obj:
					return  _error_400("Invalid Application ID in request payload")
				else:
					try:
						vals = {"application_id": app_obj.id}
						app_obj.unlink()
						return _success_200('Application deleted.',vals)
					except:
						return  _error_400("Application Not Deleted.")
			else:
				return  _error_400("Invalid Application ID in request payload")
		else:
			return  _error_400("Invalid request payload")

	@http.route('/api/application_details/multi_delete', auth='none', type="json", methods=['POST'])
	def application_details_multi_delete(self, **kwargs):
		data = request.jsonrequest
		lead_id = data.get('lead_id')
		app_id = data.get('application_id')
		vals = {}
		if lead_id and app_id:
			lead_obj = request.env['crm.lead'].sudo().search([('id','=',lead_id),('active','=',True)],limit=1)
			if not lead_obj:
				return  _error_400("Lead ID not found!!")
			active_apps = request.env['app.modeling'].sudo().search([('lead_id','=',lead_obj.id),('id','in',app_id),('active','=',True)])
			if not active_apps:
				return  _error_400("Invalid Application ID in request payload")
			try:
				active_apps.sudo().write({'active': False})
				not_deleted = [x for x in app_id if x not in active_apps.ids]
				return _success_200('Applications deleted.',str(active_apps.ids) + " has been deleted. "  +  str(not_deleted) + " deletion failed!!")
			except:
				return _error_400(str(app_id) + "Application Not Deleted.")
		else:
			return  _error_400("Invalid request payload")

class SecurityRequirements(http.Controller):

	@http.route('/api/technical_requirement/update', auth='none', type='json', methods=['POST'], csrf=False)
	def security_requirement_json(self, **kwargs):
		vals = {}
		data = request.jsonrequest
		lead_id = data.get('lead_id')
		selection_list = ['site_internet_usage',"existing_routing_protocol", "topology_requirement", "public_cloud_name"]
		for sl in selection_list:
			if data.get(sl) and data.get(sl) not in dict(request.env['crm.lead'].sudo()._fields[sl].selection).keys():
				return  _error_400("Invalid request payload")
		cpe_model_ids = []
		for cpe_product in data.get('cpe_model_ids'):
			oem_model_id = request.env['product.brands'].sudo().browse(cpe_product.get('oem_id')).exists() if cpe_product.get('oem_id') else False
			product_id = request.env['product.product'].sudo().search([('id','=',cpe_product.get('cpe_id')),('active','=',True)],limit=1) if cpe_product.get('cpe_id') else False
			if not oem_model_id or not product_id:
				return _error_400("Invalid CPE Data")
			cpe_vals = {
				"oem_model_id": oem_model_id.id if oem_model_id else False,
				"product_id": product_id.id if product_id else False,
				"no_of_devices": cpe_product.get('no_of_devices')
			}
			cpe_model_id = request.env['cpe.product'].sudo().create(cpe_vals)
			cpe_model_ids.append(cpe_model_id.id)
		security_req_ids = request.env['security.requirement'].sudo().search([('name','in',data.get('security_requirement_ids')),('active','=',True)]) if data.get('security_requirement_ids') else False
		if lead_id:
			lead = request.env['crm.lead'].sudo().search([('id','=',int(lead_id)),('active','=',True)],limit=1)
			if not lead:
				return _error_400("lead Id Not Found")
			try:
				vals = {'cpe_requirement': 'yes' if data.get('cpe_requirement') == 'true' else 'no',
						"cpe_model_ids": [(6,0,cpe_model_ids)],
						'existing_routing_protocol': data.get('existing_routing_protocol'),
						'topology_requirement': data.get('topology_requirement'),
						'site_internet_usage': data.get('site_internet_usage'),
						"is_public_cloud_access":  True if data.get("is_public_cloud_access") == 'true' else False,
						"public_cloud_name": data.get("public_cloud_name") if data.get("is_public_cloud_access") else False,
						"security_requirement_ids": [(6, 0, security_req_ids.ids)]
					}
				lead.sudo().write(vals)
				return _success_200('Technical Requirement Updated..', data)
			except:
				return _error_400("Technical Requirement Not Updated.")
		else:
			return  _error_400("Invalid request payload")

class SalesDashboard(http.Controller):
	@http.route('/api/sales_tickets/owner', methods=["GET"], auth='none')
	def sales_tickets_per_owner(self, **kwargs):
		owners = request.env['res.partner'].sudo().search([('active','=',True)])
		owner_count_mapping = {
			r['partner_id'][0]: r['partner_id_count']
			for r in request.env['crm.lead'].sudo().read_group(
				domain=[('partner_id', 'in', owners.ids)],
				fields=['partner_id'],
				groupby=['partner_id'],
			)
		}
		sales_tickets = []
		vals = {}
		for i in owner_count_mapping.items():
			owner_name = request.env['res.partner'].sudo().search([('id','=',i[0]),('active','=',True)],limit=1)
			vals = {'name': owner_name.name, 'count': i[1]}
			sales_tickets.append(vals)
		return Response(json.dumps(sales_tickets), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")

	@http.route(['/api/sales_tickets/source','/api/sales_tickets/source/<int:lead_id>','/api/sales_tickets/source/<string:stage>'], type="json", methods=["POST"], auth="none")
	def sales_tickets_per_source(self, lead_id=False, stage=False, **kw):
		try:
			data = request.jsonrequest
			sources = request.env['utm.source'].sudo().search([('active','=',True)])
			domain = [('source_id', 'in', sources.ids)]
			if len(data):
				values = data.get("filter_list")
				if values:
					domain += _get_filter_domain(values)
			if lead_id:
				domain += [('id','=',lead_id),('case_id','!=', False),('active','=',True)]
			else:
				domain += [('case_id','!=', False),('active','=',True)]
			if stage:
				domain += [('type','=',stage)]
			source_count_mapping = {
				r['source_id'][0]: r['source_id_count']
				for r in request.env['crm.lead'].sudo().read_group(
					domain=domain,
					fields=['source_id'],
					groupby=['source_id'],
				)
			}
			source_count = []
			vals = {}
			for i in sources:
				vals = {'name': i.name, 'count': source_count_mapping.get(i.id, 0)}
				source_count.append(vals)
			return _success_200('Souce Data : ', source_count)
		except Exception as e:
			return _error_400("Failed. " + str(e))

	@http.route(['/api/certainity_filter','/api/certainity_filter/<int:lead_id>','/api/certainity_filter/<string:stage>'], type="json", methods=["POST"], auth="none")
	def certainity_filter(self, lead_id=False, stage=False, **kw):
		try:
			data = request.jsonrequest
			certainity_ids = request.env['crm.certainity'].sudo().search([])
			domain = [('certainity', 'in', certainity_ids.ids)]
			if len(data):
				values = data.get("filter_list")
				if values:
					domain += _get_filter_domain(values)
			if lead_id:
				domain += [('id','=',lead_id),('case_id','!=', False),('active','=',True)]
			else:
				domain += [('case_id','!=', False),('active','=',True)]
			if stage:
				domain += [('type','=',stage)]
			certainity_count_mapping = {
				r['certainity'][0]: r['certainity_count']
				for r in request.env['crm.lead'].sudo().read_group(
					domain=domain,
					fields=['certainity'],
					groupby=['certainity'],
				)
			}
			certainity_count = []
			vals = {}
			for i in certainity_ids:
				vals = {'name': i.name, 'count': certainity_count_mapping.get(i.id, 0)}
				certainity_count.append(vals)
			return _success_200('Souce Data : ', certainity_count)
		except Exception as e:
			return _error_400("Failed. " + str(e))

	@http.route('/api/hardware_routers/<int:lead_id>', methods=["GET"], auth='none')
	def api_hardware_routers(self, lead_id, **kwargs):
		try:
			if not lead_id:
				return Response(json.dumps("Lead ID not found."), status = 403,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")
			lead_obj = request.env['crm.lead'].sudo().search([('id','=',lead_id),('active','=',True)],limit=1)
			if not lead_obj:
				return Response(json.dumps("Lead ID does not exist."), status = 403,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")
			routers_names = []
			for cpe in lead_obj.cpe_model_ids:
				router_name = str(cpe.oem_model_id.name)+'_'+str(cpe.product_id.name)
				vals = {'id': cpe.product_id.id, "name":router_name}
				routers_names.append(vals)
			return Response(json.dumps(routers_names), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")
		except MissingError:
			return Response(json.dumps("Failed"), status = 403,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")

	@http.route('/api/dynamic_generate_csv', type="json", csrf=False, methods=["POST"], auth='none')
	def dynamic_generate_csv(self, **kwargs):
		data = request.jsonrequest
		fields_data = []
		model = data.get('table_name')
		ir_model_field_obj = request.env['ir.model.fields'].sudo().search([('model', '=', model)])
		for rec in ir_model_field_obj:
			fields_data.append(rec.field_description)
		filename = '/home/in2ituser/Documents/xyz.csv'
		with open(filename, 'w', newline="") as file:
			csvwriter = csv.writer(file)
			csvwriter.writerow(fields_data)
		return _success_200('Success : ', filename)

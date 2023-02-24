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
from odoo import http, tools
from datetime import datetime
import datetime 
import re
from odoo.exceptions import ValidationError
from odoo.http import content_disposition, dispatch_rpc, request, Response

_logger = logging.getLogger(__name__)


class ProductOffering(http.Controller):
	@http.route('/product/listing', methods=["GET"], auth="none")
	def product_listing(self, **kw):
		if not request.uid:
			request.uid = odoo.SUPERUSER_ID
		values = request.params.copy()
		product_cate_obj = request.env['product.category'].sudo()
		product_obj = request.env['product.product'].sudo()
		product_templ_obj = request.env['product.template'].sudo()
		all_categ_id = product_cate_obj.search([('parent_id', '=', None)])
		finle_order_data = []
		for categ_id in all_categ_id:
			categ_details = {}
			categ_details.update({"Category" : categ_id.name})
			all_product_template_ids = product_templ_obj.search([('categ_id','=',categ_id.id)])
			all_product_list = []
			for product_template_id in all_product_template_ids.filtered(lambda p: p.is_devices != True):
				image_list = []
				image_url = '/web/image/product.template/%s/image_1920' % product_template_id.id
				image_list.append(image_url)
				product_dict = {}
				variant_dict = {}
				all_variant_list = []
				my_images = product_template_id.image_128.decode() if product_template_id.image_128 else False
				all_images_list = []
				all_images_list.append(my_images)
				product_features_list = []
				for product_features_id in product_template_id.product_features_ids:
					product_images = product_features_id.image_1920
					vals = {"id": product_features_id.id,
							"images": product_images.decode() if product_images else False,
							"name": product_features_id.name,
							"description": product_features_id.description}
					product_features_list.append(vals)
				product_dict.update({"id":product_template_id.id, "name": product_template_id.name,
					"images": all_images_list,'product_features': product_features_list })
				# for variant_id in product_obj.search([('product_tmpl_id','=', product_template_id.id)]):
				for variant_id in product_template_id.supported_devices_ids:
					# variant_dict.update({
					variant_vals = {
							"id" : variant_id.id,
							"name" : variant_id.name,
							'barcode': variant_id.barcode,
							"reference": variant_id.default_code,
							"price" : variant_id.list_price,
							"feature": ['Virtual Client Equipment(vCPE)','BOD','Wide Area Network (WAN) Optimisation','Intelligent Backend','Quick Access to Public Cloud']
							}
					all_variant_list.append(variant_vals)
				product_dict.update({"Variant":all_variant_list})
				all_product_list.append(product_dict)
			categ_details.update({"Product":all_product_list})
			finle_order_data.append(categ_details)
		return Response(json.dumps(finle_order_data), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")


class ProductErdTable(http.Controller):
	@http.route('/api/get_product_erd', methods=["GET"], auth='none')
	def get_product_erd(self, **kwargs):
		table_model = []
		ir_model_obj = request.env['ir.model'].sudo().search([('model','ilike','oss')])
		for ir_model_id in ir_model_obj:
			field_vals_list = []
			for field_id in ir_model_id.field_id:
				field_vals = {
					"field_name": field_id.name,
					"field_description": field_id.field_description,
					"field_type": field_id.ttype,
					"is_index": field_id.index
				}
				field_vals_list.append(field_vals)

			vals = {"id":ir_model_id.id , "table_name":ir_model_id.model,"fields": field_vals_list}
			table_model.append(vals)
		return Response(json.dumps(table_model), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")

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
from odoo.http import content_disposition, dispatch_rpc, request, Response

_logger = logging.getLogger(__name__)


class ACLAPI(http.Controller):
	@http.route('/order_details_api/get_phone', methods=["GET"], auth="none")
	def order_details(self, **kw):
		if not request.uid:
			request.uid = odoo.SUPERUSER_ID
		values = request.params.copy()
		sale_order_obj = request.env['sale.order'].sudo()
		partner_obj = request.env['res.partner'].sudo()
		if 'phone' in kw.keys():
			partner_id = partner_obj.search([('mobile', '=', kw["phone"])])
		if not partner_id:
			return Response(json.dumps({'message' : 'No details found'}), headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,status = 200, content_type = "application/json") 
		order_ids = sale_order_obj.search([('partner_id', '=', partner_id.id),], limit=10, order='date_order desc')
		finle_order_data = []
		for order_id in order_ids:
			order_details = {}
			gen_info={
					"order_number":order_id.name,
					"total" : order_id.amount_total,
					"completed_at" : str(order_id.create_date),
					"delivered" : 'Delivered',
					"status" : False ,
					"ship_address" : str(order_id.partner_invoice_id.street.encode('utf-8')) if order_id.partner_invoice_id.street else 'Not Found',
					"name" : str(order_id.partner_invoice_id.name.encode('utf-8')) if order_id.partner_invoice_id.name else 'Not Found',
					"phone" : str(order_id.partner_invoice_id.phone),
					"street1" : str(order_id.partner_invoice_id.street.encode('utf-8')) if order_id.partner_invoice_id.street else 'Not Found',
					"street2" : str(order_id.partner_invoice_id.street2.encode('utf-8')) if order_id.partner_invoice_id.street2 else 'Not found',
					"city" : str(order_id.partner_invoice_id.city.encode('utf-8')) if order_id.partner_invoice_id.city else 'Not Found',
					"zip" : str(order_id.partner_invoice_id.zip),
					'state' : str(order_id.partner_invoice_id.state_id.name) if order_id.partner_invoice_id.state_id.name else 'Not Found',
					'country' : str(order_id.partner_invoice_id.country_id.name) if order_id.partner_invoice_id.country_id.name else 'Not Found',
				}
			order_details.update(gen_info)
			finle_order_data.append(order_details)
		return Response(json.dumps(finle_order_data), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")

class ACLOderApi(http.Controller):
	@http.route('/order_details_api/order_no', methods=["GET"], auth="none")
	def order_details(self, **kwargs):
		pass
class ProductOffering(http.Controller):
	@http.route('/product/listing1111', methods=["GET"], auth="none")
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
			_logger.info("\n all_product_template_ids===",all_product_template_ids)
			for product_template_id in all_product_template_ids:
				# with open(product_template_id.image_128, "rb") as attachment_file:
				# 	imageBase64 = base64.b64encode(attachment_file.read())

				# with open(product_template_id.image_128, mode='rb') as file:
				#     img = file.read()
				# image['img'] = base64.encodebytes(img).decode('utf-8')
				# from odoo.tools.image import image_data_uri
				# print(image_data_uri(image))
				image_list = []
				image_url = '/web/image/product.template/%s/image_1920' % product_template_id.id
				image_list.append(image_url)
				product_dict = {}
				variant_dict = {}
				all_variant_list = []
				my_images = product_template_id.image_128
				all_images_list = []
				all_images_list.append(str(my_images))
				product_dict.update({"id":product_template_id.id, "name": product_template_id.name,
					"images": all_images_list })
				# for variant_id in product_obj.search([('product_tmpl_id','=', product_template_id.id)]):
				print("\n optional_product_ids===",product_template_id.optional_product_ids)
				for variant_id in product_template_id.optional_product_ids:
					variant_dict.update({
							"id" : variant_id.id,
							"name" : variant_id.name,
							'barcode': variant_id.barcode,
							"reference": variant_id.default_code,
							"price" : variant_id.list_price,
							"feature": ['Virtual Client Equipment(vCPE)','BOD','Wide Area Network (WAN) Optimisation','Intelligent Backend','Quick Access to Public Cloud']
							})
					all_variant_list.append(variant_dict)
					print("\n alll variant ===",all_variant_list)
				product_dict.update({"Variant":all_variant_list})
				all_product_list.append(product_dict)
			categ_details.update({"Product":all_product_list})
			finle_order_data.append(categ_details)
		return Response(json.dumps(finle_order_data), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")



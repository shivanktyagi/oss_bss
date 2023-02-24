# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2022 (https://www.in2ittech.com)
#
##############################################################################

import json
import xlrd
from odoo import http
from odoo.http import request, Response
from odoo.addons.oss_contact.controllers.contact_creation import _success_organization_200, \
    _success_organization_error_200, _success_200

def _error_403(error_msg):
    return {
        'success': False,
        'status': 'Already exists',
        'code': 403,
        'response': error_msg
    }
    
def _error_404(error_msg):
    return {
        'success': False,
        'status': 'Not Found',
        'code': 404,
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

class DynamicTableCreation(http.Controller):
    @http.route('/api/get_all_dynamic_table', methods=["GET"], auth='none')
    def all_dynamic_table(self, **kwargs):
        table_model = []
        ir_model_obj = request.env['ir.model'].sudo().search([('from_api','=',True)])
        for ir_model_id in ir_model_obj:
            field_vals_list = []
            for field_id in ir_model_id.field_id:
                field_vals = {
                    "field_name": field_id.name if field_id.name else '',
                    "field_description": field_id.field_description if field_id.field_description else '',
                    "field_type": field_id.ttype if field_id.ttype else '',
                    "is_index": field_id.index if field_id.index else '',
                    "Created By": field_id.create_uid.name if field_id.create_uid else '', 
                    "Created On": field_id.create_date.strftime('%d/%m/%Y') if field_id.create_date else '', 
                    "Updated By": field_id.write_uid.name if field_id.write_uid else '', 
                    "Updated On": field_id.write_date.strftime('%d/%m/%Y') if field_id.write_date else '', 
                }
                field_vals_list.append(field_vals)
            vals = {"id":ir_model_id.id , 
            "Name":ir_model_id.model,
            "Label": ir_model_id.name,
            "Description": ir_model_id.description,
            "Created By": ir_model_id.create_uid.name if ir_model_id.create_uid else '', 
            "Created On": ir_model_id.create_date.strftime('%d/%m/%Y') if ir_model_id.create_date else '', 
            "Updated By": ir_model_id.write_uid.name if ir_model_id.write_uid else '', 
            "Updated On": ir_model_id.write_date.strftime('%d/%m/%Y') if ir_model_id.write_date else '', 
            "Fields": field_vals_list}
            table_model.append(vals)
        return Response(json.dumps(table_model), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")

    @http.route('/api/get_all_tables', methods=["GET"], auth='none')
    def get_all_tables(self, **kwargs):
        try:
            params = request.params
            domain = [('from_api', '=', True)]
            if params.get('search_filter'):
                domain += [('name','ilike',params.get('search_filter'))]
            if params.get('is_standard') and params.get('is_standard') == "true":
                domain = [('table_type','=','is_standard')] + domain
            if params.get('is_custom') and params.get('is_custom') == "true":
                domain = [('table_type','=','is_custom')] + domain
            if (params.get('is_standard') and params.get('is_standard') == "true") and (params.get('is_custom') and params.get('is_custom') == "true"):
                domain = ['|'] + domain
            limit = None
            offset = None
            if params.get('max_page') and params.get('min_page'):
                limit = int(params.get('max_page')) - int(params.get('min_page'))
                offset = int(params.get('min_page'))
            model_obj = request.env['ir.model'].sudo()
            count = model_obj.search_count(domain)
            ir_model_obj = model_obj.search(domain, order='id desc', limit=limit, offset=offset)
            table_model = []
            if not ir_model_obj:
                return Response(json.dumps({"total_record": count, 'data': table_model}), status = 200,
                            headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,
                            content_type = "application/json")
            for ir_model_id in ir_model_obj:
                ir_model_fields_obj = request.env['ir.model.fields'].sudo().search([('model_id', '=', ir_model_id.id)])
                rows_count = request.env[ir_model_id.model].sudo().search_count([('id', '!=', None)])
                if not ir_model_fields_obj:
                    vals = {
                        'success': False,
                        'status': str(f"Model ID '{ir_model_id.id}' in table 'ir.model.fields' does not exist !"),
                        'code': 404,
                    }
                    return Response(json.dumps(vals), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")
                attribute_count = len(ir_model_fields_obj)
                vals = {
                    "table_id": {"value":ir_model_id.id, "is_edit": False, "type":ir_model_id.fields_get().get('id')['type']},
                    "table_type": {"value": ir_model_id.table_type, "is_edit": False, "type":"boolean"},
                    "table_name": {"value":ir_model_id.name, "is_edit": True, "type":ir_model_id.fields_get().get('name')['type']},
                    "description": {"value":ir_model_id.description, "is_edit": True, "type":ir_model_id.fields_get().get('description')['type']},
                    "attribute_count": {"value":attribute_count, "is_edit": False, "type":"integer"},
                    "rows_count": {"value":rows_count, "is_edit": False, "type":"integer"},
                    "created_on": {"value":ir_model_id.create_date.strftime('%d/%m/%Y') if ir_model_id.create_date else '',"is_edit": False, "type":ir_model_id.fields_get().get('create_date')['type']},
                    "created_by": {"value":ir_model_id.created_by if ir_model_id.created_by else '',"is_edit": False, "type":ir_model_id.fields_get().get('created_by')['type']},
                    "updated_on": {"value":ir_model_id.write_date.strftime('%d/%m/%Y') if ir_model_id.write_date else '',"is_edit": False, "type":ir_model_id.fields_get().get('write_date')['type']},
                    "updated_by": {"value":ir_model_id.write_uid.name if ir_model_id.write_uid else '',"is_edit": False, "type":ir_model_id.fields_get().get('write_uid')['type']},
                    "is_standard":{"value":True,"is_edit": False, "type":"boolean"},
                    "is_active": {"value":True,"is_edit": False, "type":"boolean"}
                }
                table_model.append(vals)
            return Response(json.dumps({"total_record": count, 'data': table_model}), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")
        except Exception as e:
            vals = {
                'success': False,
                'status': 'Failed Due To: ' + str(e),
                'code': 404,
            }
            return Response(json.dumps(vals), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")
 
    @http.route('/api/dynamic_table_creation', type="json", csrf=False, methods=["POST"], auth='none')
    def dynamic_table_create(self, **kwargs):
        data = request.jsonrequest
        t_name = data.get('table_name')
        t_description = data.get('table_description')
        if t_name and t_description:
            ir_model_obj = request.env['ir.model'].sudo()
            tbl_name = t_name.lower().replace(" ", ".")
            vals = {
                "name": data.get('table_label'),
                "description": t_description,
                "model": tbl_name,
                "order": 'id',
                # "state": "base",
                "from_api": True
            }
            try:
                table_obj = ir_model_obj.create(vals)
                if table_obj:
                    vals.update({'id':table_obj.id})
                    return _success_200("Table Created.", vals)
            except Exception as e:
                return _error_400("Table not Created." + str(e))
        else:
            return  _error_400("Invalid request payload")

    @http.route('/api/dynamic_standard_table_creation', type="json", csrf=False, methods=["POST"], auth='none')
    def dynamic_standard_table_create(self, **kwargs):
        data = request.jsonrequest
        tables = data.get('tables')
        requested_data = []
        response_vals = {}
        success = []
        fail = []
        ir_model_obj = request.env['ir.model'].sudo()
        if tables:
            try:
                for tb in tables:
                    try:
                        t_name = tb.get('table_name')
                        t_description = tb.get('description')
                        created_by = tb.get('created_by')
                        tbl_name = t_name.lower().replace(" ", ".")
                        table_type = False
                        if tb.get('is_standard'):
                            table_type = 'is_standard'
                        elif tb.get('is_custom'):
                            table_type = 'is_custom'
                        else:
                            table_type = False
                        vals = {
                            "name": t_name,
                            "model": tbl_name,
                            "description": t_description,
                            "order": 'id',
                            "from_api": True,
                            # 'state': 'base',
                            'create_uid': 2,
                            'created_by': created_by,
                            'table_type': table_type,
                        }
                        table_exist = ir_model_obj.sudo().search([('model', '=', tbl_name)], limit=1).exists()
                        if table_exist:
                            table_exist_vals = {
                                "table_id": {"value": table_exist.id, "is_edit": False,
                                             "type": table_exist.fields_get().get('id')['type']},
                                "table_type": {"value": table_exist.table_type, "is_edit": False, "type":"boolean"},
                                "table_name": {"value": table_exist.name, "is_edit": True,
                                               "type": table_exist.fields_get().get('name')['type']},
                                "description": {"value": table_exist.description, "is_edit": True,
                                                "type": table_exist.fields_get().get('description')['type']},
                                "created_on": {
                                    "value": table_exist.create_date.strftime(
                                        '%d/%m/%Y') if table_exist.create_date else '',
                                    "is_edit": False, "type": table_exist.fields_get().get('create_date')['type']},
                                "created_by": {"value": table_exist.created_by if table_exist.created_by else '',
                                               "is_edit": False,
                                               "type": table_exist.fields_get().get('created_by')['type']},
                                "updated_on": {
                                    "value": table_exist.write_date.strftime(
                                        '%d/%m/%Y') if table_exist.write_date else '',
                                    "is_edit": False, "type": table_exist.fields_get().get('write_date')['type']},
                                "updated_by": {"value": table_exist.write_uid.name if table_exist.write_uid else '',
                                               "is_edit": False,
                                               "type": table_exist.fields_get().get('write_uid')['type']},
                                "is_standard": {"value": True, "is_edit": False, "type": "boolean"},
                                "is_active": {"value": True, "is_edit": False, "type": "boolean"}
                            }
                            fail.append(table_exist_vals)
                        else:
                            table_obj = ir_model_obj.with_context(from_api=True).create(vals)
                            if table_obj:
                                table_create_vals = {
                                    "table_id": {"value": table_obj.id, "is_edit": False,
                                                 "type": table_obj.fields_get().get('id')['type']},
                                    "table_type": {"value": table_obj.table_type, "is_edit": False, "type":"boolean"},
                                    "table_name": {"value": table_obj.name, "is_edit": True,
                                                   "type": table_obj.fields_get().get('name')['type']},
                                    "description": {"value": table_obj.description, "is_edit": True,
                                                    "type": table_obj.fields_get().get('description')['type']},
                                    "created_on": {
                                        "value": table_obj.create_date.strftime(
                                            '%d/%m/%Y') if table_obj.create_date else '',
                                        "is_edit": False, "type": table_obj.fields_get().get('create_date')['type']},
                                    "created_by": {"value": table_obj.created_by if table_obj.created_by else '',
                                                   "is_edit": False,
                                                   "type": table_obj.fields_get().get('created_by')['type']},
                                    "updated_on": {
                                        "value": table_obj.write_date.strftime(
                                            '%d/%m/%Y') if table_obj.write_date else '',
                                        "is_edit": False, "type": table_obj.fields_get().get('write_date')['type']},
                                    "updated_by": {"value": table_obj.write_uid.name if table_obj.write_uid else '',
                                                   "is_edit": False,
                                                   "type": table_obj.fields_get().get('write_uid')['type']},
                                    "is_standard": {"value": True, "is_edit": False, "type": "boolean"},
                                    "is_active": {"value": True, "is_edit": False, "type": "boolean"}
                                }
                                success.append(table_create_vals)
                    except Exception as e:
                        return _error_400("Failed : "+ str(e))
                response_vals['table_already_exist'] = fail
                response_vals['table_created'] = success
                requested_data.append(response_vals)
                if requested_data:
                    return _success_200("Done", requested_data)
            except Exception as e:
                return _error_400("Table not Created." + str(e))
        else:
            return _error_400("Invalid request payload")

    @http.route('/api/dynamic_fields', type="json", csrf=False, methods=["POST"], auth='none')
    def dynamic_fields(self, **kwargs):
        data = request.jsonrequest
        ir_model_field_obj = request.env['ir.model.fields'].sudo()
        ir_model_obj = request.env['ir.model'].sudo()
        fields = data.get('fields')
        table_name_id = data.get('table_name_id')
        success = []
        fail = []
        if table_name_id and fields:
            table_id = ir_model_obj.browse(table_name_id).exists()
            if not table_id:
                return _error_400("Table not found.")
            for i in fields:
                try:
                    attribute_name = i.get('attribute_name')
                    field_type = i.get('attribute_type')
                    properties = i.get('properties')
                    field_vals = {
                        'name': "x_" + attribute_name.lower().replace(" ", "_"), 
                        'field_description': attribute_name, 
                        'description': i.get('description'),
                        'model_id': table_id.id, 
                        'ttype': field_type, 
                        'required': True if "required" in properties else False,
                        'readonly': False, 
                        'date_format': i.get('format'),
                        'index': True if "index" in properties else False,
                        'is_unique': True if "is_unique" in properties else False,
                        'foreign_key': True if "foreign_key" in properties else False, 
                        'primary_key': True if "primary_key" in properties else False, 
                        "from_api": True,
                        "size": i.get('size'),
                        "limit_min": i.get('limit_min'),
                        "limit_max": i.get('limit_max'),
                    }
                    if 'foreign_key' in properties or i.get('relation') in ['many2one','many2many','one2many']:
                        if not i.get('selected_table_id'):
                            fail.append("Selected Table name is required for creating fields of type 'Many2one' and 'Many2many'")
                            continue
                        selected_table_obj = ir_model_obj.browse(i.get('selected_table_id')).exists()
                        if not selected_table_obj:
                            fail.append("Selected Table name is required for creating fields of type 'Many2one' and 'Many2many'")
                            continue
                        if not i.get('relation'):
                            fail.append("Relation is required for creating fields of type 'Many2one' and 'Many2many'")
                            continue
                        field_vals['ttype'] = i.get('relation')
                        field_vals['relation'] = selected_table_obj.model
                        if field_type == 'one2many' and not i.get('selected_attribute'):
                            fail.append("Attribute is required for creating fields of type 'Many2one' and 'Many2many'")
                            continue
                        if i.get('selected_attribute') not in selected_table_obj.field_id.mapped('name'):
                            fail.append("Attribute not found for creating fields of type 'Many2one' and 'Many2many'")
                            continue
                        field_vals['relation_field'] = i.get('selected_attribute')
                    fields_obj = ir_model_field_obj.create(field_vals)
                    if fields_obj:
                        success.append(fields_obj.id)
                except Exception as e:
                    fail.append(str(e))
            msg = "No Fields Created."
            if success:
                msg = str(success) + " Fields Created."
            return _success_200(msg, fail)
        else:
            return  _error_400("Invalid request payload")

    @http.route('/api/dynamic_attribute_delete', type="json", csrf=False, methods=["POST"], auth='none')
    def dynamic_attribute_delete(self, **kwargs):
        data = request.jsonrequest
        ir_model_obj = request.env['ir.model'].sudo()
        ir_model_field_obj = request.env['ir.model.fields'].sudo()
        table_id = data.get('table_id')
        field_id = data.get('attribute_id')
        if table_id and field_id:
            table_obj = ir_model_obj.browse(table_id).exists()
            if not table_obj:
                return _error_400("Table not found.")
            field_obj = ir_model_field_obj.search([('model_id','=',table_obj.id),('id','in',field_id)])
            if not field_obj:
                return _error_400("Attribute not found.")
            try:
                field_obj.sudo().unlink()
                return _success_200("Attributes Deleted", {"Deleted Attributes": field_obj.ids})
            except Exception as e:
                return _error_400("Attributes Not Deleted. " + str(e))
        else:
            return _error_400("Invalid request payload")

    @http.route('/api/dynamic_table_update', type="json", csrf=False, methods=["POST"], auth='none')
    def dynamic_table_update(self, **kwargs):
        data = request.jsonrequest
        t_id = data.get('table_id')
        t_description = data.get('table_description')
        if t_id and t_description:
            ir_model_obj = request.env['ir.model'].sudo()
            table_obj = ir_model_obj.browse(t_id).exists()
            if not table_obj:
                return _error_400("Table Not found")
            vals = {
                "name": data.get('table_label'),
                "description": t_description,
            }
            try:
                table_obj.write(vals)
                return _success_200("Table Updated.", vals)
            except:
                return _error_400("Table not updated.")
        else:
            return  _error_400("Invalid request payload")

    @http.route('/api/dynamic_standard_table_update', type="json", csrf=False, methods=["POST"], auth='none')
    def dynamic_standard_table_update(self, **kwargs):
        data = request.jsonrequest
        tables = data.get('tables')
        success  = []
        fail = []
        ir_model_obj = request.env['ir.model'].sudo()
        if tables:
            try:
                for tb in tables:
                    try:
                        t_id = tb.get('table_id')
                        t_description = tb.get('description')
                        table_obj = ir_model_obj.browse(t_id).exists()
                        if not table_obj:
                            return _error_400("Table Not found")
                        vals = {
                            "name": tb.get('table_name'),
                            "description": t_description,
                        }
                        table_obj.write(vals)
                        success.append(table_obj.id)
                    except Exception as e:
                        fail.append(str(e))
                msg = "No Tables Created."
                if success:
                    msg = str(success) + " Tables Updated."
                return _success_200(msg, fail)
            except Exception as e:
                return _error_400("Table not Updated." + str(e))
        else:
            return  _error_400("Invalid request payload")

    @http.route('/api/dynamic_table_delete', type="json", csrf=False, methods=["POST"], auth='none')
    def dynamic_table_delete(self, **kwargs):
        data = request.jsonrequest
        t_id = data.get('table_id')
        if t_id:
            ir_model_obj = request.env['ir.model'].sudo()
            table_obj = ir_model_obj.browse(t_id).exists()
            if not table_obj:
                return _error_400("Table Not found")
            try:
                table_obj.unlink()
                return _success_200("Table Deleted.",{})
            except Exception as e:
                return _error_400("Table not deleted. " + str(e))
        else:
            return  _error_400("Invalid request payload")
    
    @http.route('/api/dynamic_table_clone', type="json", csrf=False, methods=["POST"], auth='none')
    def dynamic_table_clone(self, **kwargs):
        data = request.jsonrequest
        t_id = data.get('table_id')
        new_table_model = data.get('new_table_model')
        new_table_name = data.get('new_table_name')
        if t_id:
            ir_model_obj = request.env['ir.model'].sudo()
            table_obj = ir_model_obj.browse(t_id).exists()
            if not table_obj:
                return _error_400("Table Not found")
            try:
                new_table = table_obj.copy(default={'state':'base',"model": new_table_model, "name": new_table_name})
                return _success_200("Table Cloned.",{'new_table': new_table.id})
            except Exception as e:
                return _error_400("Table not Cloned. " + str(e))
        else:
            return  _error_400("Invalid request payload")

    @http.route('/api/dynamic_fields_update', type="json", csrf=False, methods=["POST"], auth='none')
    def dynamic_fields_update(self, **kwargs):
        data = request.jsonrequest
        ir_model_field_obj = request.env['ir.model.fields'].sudo()
        ir_model_obj = request.env['ir.model'].sudo()
        fields = data.get('fields')
        table_name_id = data.get('table_name_id')
        success = []
        fail = []
        if table_name_id and fields:
            table_id = ir_model_obj.browse(table_name_id).exists()
            if not table_id:
                return _error_400("Table not found.")
            for i in fields:
                try:
                    fl_id = ir_model_field_obj.browse(i.get('attribute_id')).exists()
                    if not fl_id:
                        fail.append(str(i.get('attribute_id')) + " Not Found. ")
                    attribute_name = i.get('attribute_name')
                    field_vals = {
                        'name': "x_" + attribute_name.lower().replace(" ", "_"), 
                        'field_description': attribute_name, 
                        'description': i.get('description'),
                        'model_id': table_id.id,
                        "size": i.get('size'),
                        "limit_min": i.get('limit_min'),
                        "limit_max": i.get('limit_max'),
                    }
                    fields_obj = fl_id.sudo().write(field_vals)
                    if fields_obj:
                        success.append(fl_id.id)
                except Exception as e:
                    fail.append(str(e))
            msg = "No Fields Updated."
            if success:
                msg = str(success) + " Fields Updated."
            return _success_200(msg, fail)
        else:
            return  _error_400("Invalid request payload")

    @http.route('/api/dynamic_table_record_create', type="json", csrf=False, methods=["POST"], auth='none')
    def dynamic_table_record_create(self, **kwargs):
        data = request.jsonrequest
        ir_model_obj = request.env['ir.model'].sudo()
        table_id = data.get('table_id')
        vals = data.get('data')
        if table_id and vals:
            table_obj = ir_model_obj.sudo().browse(table_id).exists()
            if not table_obj:
                return _error_400("Table not found.")
            try:
                for val in vals:
                    rec_id = request.env[table_obj.model].sudo().create(val)
                    val.update({'record_id': rec_id.id})
                return _success_200("New Record Created.", data)
            except Exception as e:
                return _error_400("Record not Created. " + str(e))
        else:
            return  _error_400("Invalid request payload")

    @http.route('/api/dynamic_table_record_update', type="json", csrf=False, methods=["POST"], auth='none')
    def dynamic_table_record_update(self, **kwargs):
        data = request.jsonrequest
        ir_model_obj = request.env['ir.model'].sudo()
        table_id = data.get('table_id')
        vals = data.get('data')
        success = []
        if table_id and vals:
            table_obj = ir_model_obj.browse(table_id).exists()
            if not table_obj:
                return _error_400("Table not found.")
            try:
                for val in vals:
                    if not val.get('record_id'):
                        return _error_400("Record ID missing.")
                    record_obj = request.env[table_obj.model].browse(val.get('record_id')).exists()
                    if not record_obj:
                        return _error_400("Record not found.")
                    del val['record_id']
                    record_obj.sudo().write(val)
                    val.update({'record_id': record_obj.id})
                    success.append(record_obj.id)
                return _success_200(str(success) + " Record Updated.", data)
            except Exception as e:
                return _error_400("Record not Updated. " + str(e))
        else:
            return  _error_400("Invalid request payload")

    @http.route('/api/dynamic_table_record_delete', auth='none', type="json", methods=['POST'])
    def dynamic_table_record_delete(self, **kwargs):
        data = request.jsonrequest
        ir_model_obj = request.env['ir.model'].sudo()
        table_id = data.get('table_id')
        record_id = data.get('record_id')
        if table_id and record_id:
            table_obj = ir_model_obj.browse(table_id).exists()
            if not table_obj:
                return _error_400("Table not found.")
            record_obj = request.env[table_obj.model].browse(record_id).exists()
            if not record_obj:
                return _error_400("Record not found.")
            try:
                record_obj.sudo().unlink()
                return _success_200("Records Deleted", {"Deleted Records": record_obj.ids})
            except Exception as e:
                return _error_400("Records Not Deleted. " + str(e))
        else:
            return _error_400("Invalid request payload")

    @http.route('/api/dynamic_record_bulk_uplode', auth='none', csrf=False, methods=['POST'])
    def dynamic_record_bulk_uplode(self, **kwargs):
        xls_file = kwargs.get('file', False)
        sheet_table_id = kwargs.get('table_id', False)
        if xls_file and sheet_table_id:
            file_extension = xls_file.filename.split('.')[-1] if xls_file and xls_file.filename else False
            if file_extension not in ['xls', 'xlsx']:
                return Response(json.dumps("Only XLS or XLSX File extension allowed"), status=200,
                                headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                                content_type="application/json")
            try:
                xls_data = xls_file.read()
                book = xlrd.open_workbook(file_contents=xls_data)
                table_name = book.sheet_names()
                fail_data = []
                success = []
                res = json.loads(sheet_table_id)
                for sheet_name in table_name:
                    table_id = request.env['ir.model'].sudo().search([('name', '=', sheet_name),('from_api','=',True)], limit=1)
                    fail_list = {"table_id":0,"sheet": sheet_name}
                    if not table_id:
                        fail_list.update({"reason": "Sheet '%s' not found." % sheet_name})
                        fail_data.append(fail_list)
                    else:
                        if table_id.id in res:
                            fail_list = {"table_id": table_id.id,"sheet": sheet_name}
                            sheet = book.sheet_by_name(sheet_name)
                            data = [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]
                            header = data[0] if len(data) >= 1 else []
                            csv_data = data[1:] if len(data) >= 2 else []
                            if len(header) == 0:
                                fail_list.update({"header": [], "data": [], "reason": "Header not defined"})
                                fail_data.append(fail_list)
                            elif len(csv_data) == 0:
                                fail_list.update({"header": header.copy(), "data": [], "reason": "Data not defined"})
                                fail_data.append(fail_list)
                            else:
                                fail_list.update({"header": header.copy(), 'data': []})
                                data_uploaded = []
                                all_fields = table_id.field_id.mapped('field_description')
                                all_req_fields = table_id.field_id.filtered(lambda arf: arf.required==True).mapped('field_description')
                                if any(i not in header for i in all_req_fields):
                                    fail_list = {"table_id": table_id.id, "sheet": sheet_name, "reason": f"Required fields {all_req_fields} missing in header"}
                                    fail_data.append(fail_list)
                                else:
                                    if all(i in all_fields for i in header):
                                        new_header = header.copy()
                                        field_names = {header.index(field.field_description): field.name for field in table_id.field_id if field.field_description in header}
                                        for k, v in field_names.items():
                                            header[k] = v
                                        for i in range(0, len(csv_data)):
                                            success_list = dict(zip(new_header, csv_data[i])) if len(csv_data) > 0 else []
                                            fail_list_data = success_list.copy()
                                            try:
                                                data_list = dict(zip(header, csv_data[i]))
                                                for f in table_id.field_id:
                                                    model_id = request.env['ir.model'].sudo().search(
                                                        [('model', '=', f.relation)],
                                                        limit=1)
                                                    if f.name in header and f.required == True and not data_list[f.name]:
                                                        fail_list_data['reason'] = f"Required field '{f.field_description}' cannot be empty!"
                                                    if f.name in header and f.ttype in ['many2many', 'one2many']:
                                                        s = data_list[f.name]
                                                        search_field = 'name' if 'name' in model_id.field_id.mapped(
                                                            'name') else 'x_name'
                                                        rel_data = request.env[f.relation].sudo().search(
                                                            [(search_field, '=', s)],
                                                            limit=1).ids
                                                        if len(rel_data) < 1:
                                                            fail_list_data['reason'] = "Field value '" + str(
                                                                f.field_description) + "' not found"
                                                        else:
                                                            data_list[f.name] = [(6, 0, rel_data)] if len(
                                                                rel_data) >= 1 else False
                                                    elif f.name in header and f.ttype in ['many2one']:
                                                        search_field = 'name' if 'name' in model_id.field_id.mapped(
                                                            'name') else 'x_name'
                                                        rel_data = request.env[f.relation].sudo().search(
                                                            [(search_field, '=', data_list[f.name])], limit=1).id
                                                        if rel_data:
                                                            data_list[f.name] = rel_data
                                                        else:
                                                            fail_list_data['reason'] = "Field value '" + str(
                                                                f.field_description) + "' not found"
                                                if fail_list_data.get('reason'):
                                                    fail_list['data'] += [fail_list_data]
                                                else:
                                                    rec = request.env[table_id.model].sudo().create(data_list)
                                                    data_uploaded.append(rec.id)
                                            except Exception as e:
                                                fail_list_data['reason'] = str(e)
                                                fail_list['data'] += [fail_list_data]
                                        if fail_list.get('data'):
                                            fail_data.append(fail_list)
                                    else:
                                        invalid_header = False
                                        for i in header:
                                            if i not in table_id.field_id.mapped('field_description'):
                                                invalid_header = i
                                        fail_list['reason'] = "Invalid Header: " + str(
                                            invalid_header) if invalid_header else "Invalid Header"
                                        fail_data.append(fail_list)
                                if len(data_uploaded)>0:
                                    success_list = {"table_id": table_id.id, "table_name": sheet_name, "rows_updated": len(data_uploaded),
                                                    "rows_error": len(fail_list['data'])}
                                    success.append(success_list)
                        else:
                            fail_list = {"table_id": 0,"sheet": sheet_name, "reason": f"Sheet ID {table_id.id} Not exist in Table List {sheet_table_id}"}
                            fail_data.append(fail_list)
                return Response(json.dumps(
                    _success_200("New Record Created.", {'Success': success, 'Fail': fail_data})),
                    headers={"Content-Type": "application/json",
                             "Access-Control-Allow-Origin": '*'},
                    content_type="application/json")
            except Exception as e:
                return Response(json.dumps(_error_400(f'You Entered Invalid Data, {str(e)}. ')),
                    headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                    content_type="application/json")
        else:
            return Response(json.dumps(_error_400("Invalid request payload, file or table_id not exist ")),
                headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                content_type="application/json")


class DevelopToQuotation(http.Controller):
    @http.route('/api/develop_summary', methods=["GET"], auth='none')
    def develop_summary(self, **kwargs):
        try:
            sale_order_lines = {}
            data = request.params.copy()
            lead_id = data.get('lead_id')
            if not lead_id: 
                return Response(json.dumps({"Failed":"Lead ID not found."}), status=403,
                                headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                                content_type="application/json")
            lead_obj = request.env['crm.lead'].sudo().search([('id', '=', lead_id), ('active', '=', True)], limit=1)
            if not lead_obj:
                return Response(json.dumps({"Failed":"Lead ID does not exist."}), status=403,
                                headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                                content_type="application/json")
            lead_obj.progress_bar = 'develop'
            product_obj = request.env['product.product'].sudo().search([('topology_type', '=', lead_obj.topology_requirement)])
            if not product_obj:
                return Response(json.dumps({"Failed": "Product ID not found."}), status=403,
                                headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                                content_type="application/json")
            if not lead_obj.partner_id:
                return Response(json.dumps({"Failed": "Partner ID in Lead not found."}), status=403,
                                headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                                content_type="application/json")
            sale_order_vals = {
                "partner_id": lead_obj.partner_id.id,
                "progress_bar": 'propose',
                "opportunity_id": lead_obj.id,
                "case_id": lead_obj.case_id,
                "medium_id": lead_obj.medium_id.id,
                "origin": lead_obj.name,
                "source_id": lead_obj.source_id.id,
                "tag_ids": [(6, 0, lead_obj.tag_ids.ids)],
                "campaign_id": lead_obj.campaign_id.id,
                "company_id": lead_obj.company_id.id,
            }
            sale_order_obj = request.env['sale.order'].sudo().create(sale_order_vals)
            ol = []
            for rec in product_obj:
                sale_order_obj.order_line = [(0, 0, {
                            'name': rec.name,
                            'product_id': rec.id,
                            'product_uom_qty': 1,
                            'product_uom': rec.uom_po_id.id,
                            'price_unit': rec.lst_price,
                            'properties': 'cloud',
                            'frequency_type': 'nrc',
                            'frequency_count': 1,
                            'tax_value': 100,
                            'discount_type': 'standard',
                        })]
            headers = ['Items', 'Properties', 'Measurement Unit', 'Price Per Unit', 'Quantity', 'Frequency Type', 'Frequency Count',
                       'Tax Type', 'Tax', 'Tax Value', 'Discount Type', 'Discount', 'Total Amount']
            ol.append({"Header" :headers})
            for line in sale_order_obj.order_line:
                ol.append({"product_id": line.product_id.id if line.product_id else "",
                                         "properties": line.properties if line.properties else "",
                                         "product_uom": line.product_uom.id if line.product_uom else "",
                                         "price_unit": line.price_unit if line.price_unit else "",
                                         "product_uom_qty": line.product_uom_qty if line.product_uom_qty else "",
                                         "frequency_type": line.frequency_type if line.frequency_type else "",
                                         "frequency_count": line.frequency_count if line.frequency_count else "",
                                         "tax_type": line.tax_type if line.tax_id else "",
                                         "tax": line.tax_id.name if line.tax_id else "",
                                         "tax_value": line.tax_value if line.tax_id else "",
                                         "discount_type": line.discount_type if line.discount_type else "",
                                         "discount_value": line.discount if line.discount else "",
                                         "total_amount": line.price_subtotal if line.price_subtotal else "",
                                         })
            sale_order_lines['summary'] = ol
            develop_state_vals = {
                # "product_package": "",
                'purchase_process': lead_obj.purchase_process if lead_obj.purchase_process else "",
                "est_delivery_date": lead_obj.date_deadline if lead_obj.date_deadline else "",
                "contract_duration": lead_obj.contract_duration if lead_obj.contract_duration else "",
                "currency": [{"id": lead_obj.currency_id.id if lead_obj.currency_id else "",
                              'name': lead_obj.currency_id.name if lead_obj.currency_id else ''}],
                'estimated_budget': lead_obj.estimated_budget if lead_obj.estimated_budget else "",
                "expected_delivery_timeframe": [
                    {"from_date": lead_obj.expected_delivery_date if lead_obj.expected_delivery_date else "",
                     'to_date': lead_obj.to_delivery_date if lead_obj.to_delivery_date else ''}],
                "priority": lead_obj.priority if lead_obj.priority else "",
                "certainity": [{"id": lead_obj.certainity.id if lead_obj.certainity else "",
                              'name': lead_obj.certainity.name if lead_obj.certainity else ''}],
                'estimated_revenue': lead_obj.estimate_revenue if lead_obj.estimate_revenue else "",
                'offered_discount': lead_obj.offered_discount if lead_obj.offered_discount else "",
                "total_nrc": lead_obj.total_nrc if lead_obj.total_nrc else '',
                "total_mrc": lead_obj.total_mrc if lead_obj.total_mrc else '',
                "total_yrc": lead_obj.total_rc if lead_obj.total_rc else '',
                'payment_mode': lead_obj.payment_mode if lead_obj.payment_mode else "",
                'closure_date': lead_obj.closure_date if lead_obj.closure_date else "",
            }
            sale_order_lines.update(develop_state_vals)
            return Response(json.dumps(sale_order_lines), status=200,
                            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")
        except Exception as e:
            return Response(json.dumps({"Failed " : str(e)}), status=400,
                            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")

    @http.route('/api/export_xls', methods=["POST"], auth='none', type='json')
    def export_xls(self, **kwargs):
        try:
            requested_data = []
            data = request.jsonrequest
            table_id = data.get('table_id')
            if not table_id: 
                return _error_400('Table ID not found.')
            for tbl_id in table_id:
                model_obj = request.env['ir.model'].sudo().search([('id', '=', tbl_id)], limit=1)
                if not model_obj:
                    continue
                field_obj = request.env['ir.model.fields'].sudo().search([('model_id', '=', tbl_id)])
                if not field_obj:
                    return _error_404(f"Model ID '{tbl_id}' in table 'ir.model.fields' does not exist !")
                attribute_label_list = []
                attribute_name_list = []
                required_attribute_list = ['id', 'create_date', 'create_uid', 'write_date', 'write_uid', '__last_update', 'display_name']
                for field in field_obj:
                    if field.name not in required_attribute_list:
                        attribute_label_list.append(field.field_description)
                        attribute_name_list.append(field.name)
                table_vals = {
                    "table_id": tbl_id,
                    "table_name": model_obj.name if model_obj.name else "",
                    "model_name": model_obj.model if model_obj.model else "",
                    "attribute_label": attribute_label_list,
                    "attribute_name": attribute_name_list
                }
                requested_data.append(table_vals)
            return _success_200('Table Data Fetch Successfully !', requested_data)
        except Exception as e:
            return _error_400('Failed: ' + str(e))

    @http.route('/api/select_attribute/dropdown', methods=["POST"], auth='none', type='json')
    def select_attribute_dropdown(self, **kwargs):
        try:
            requested_data = []
            unnecessary_fields = ['create_uid', 'create_date', 'write_uid', 'write_date', '__last_update']
            data = request.jsonrequest
            table_id = data.get('table_id')
            selected_table_id = data.get('selected_table_id')
            if not (table_id or selected_table_id):
                return _error_404('Table ID or Selected Table ID not found.')
            table_obj = request.env['ir.model'].sudo().search([('id', '=', table_id)]).exists()
            if not table_obj:
                return _error_404(f"Table ID '{table_id}' does not exist !")
            selected_obj = request.env['ir.model'].sudo().search([('id', '=', selected_table_id)]).exists()
            if not selected_obj:
                return _error_404(f"Selected Table ID '{selected_table_id}' does not exist !")
            ir_field_obj = selected_obj.field_id.filtered(lambda obj: obj.relation == table_obj.model and obj.ttype == 'many2one')
            if not ir_field_obj:
                return _success_200("Requested Data Fetch Successfully !",[])
            for field in ir_field_obj:
                if field.name not in unnecessary_fields:
                    field_vals = {
                        "id": field.name if field.name else '',
                        "name": field.field_description if field.field_description else '',
                    }
                    requested_data.append(field_vals)
            return _success_200('Requested Data Fetch Successfully !', requested_data)
        except Exception as e:
            return _error_404('Failed: ' + str(e))

    @http.route('/api/get_attribute_table', methods=["POST"], auth='none', type='json')
    def get_attribute_table(self):
        try:
            requested_data = []
            data = request.jsonrequest
            table_id = data.get('table_id')
            if table_id :
                api_table = request.env['ir.model'].sudo().search([('id','=',int(table_id)),('from_api','=',True)]).exists()
            if not table_id or not api_table:
                return _success_200('Table ID not found.',[])
            field_obj = request.env['ir.model.fields'].sudo().search([('model_id', '=', table_id)])
            for field in field_obj:
                property_list = []
                if field.required:
                    property_list.append({"id":"required", "name":"Mandatory"})
                if field.index:
                    property_list.append({"id":"index", "name":"Index"})
                if field.is_unique:
                    property_list.append({"id":"is_unique", "name":"Unique"})
                if field.foreign_key:
                    property_list.append({"id":"foreign_key", "name":"Foreign Key"})
                if field.primary_key or field.name == 'id':
                    property_list.append({"id":"primary_key", "name":"Primary Key"})
                table_vals = {
                    "attribute_id": {"value":field.id,"is_edit":False,"is_delete":False if field.state == 'base' else True,"type":"integer"},
                    "properties": {"value":property_list,"is_edit":False,"type":"integer"},
                    "attribute_name": {"value": field.field_description, "is_edit": True, "type": api_table.fields_get().get('name')['type']},
                    "description": {"value": field.description if field.description else "", "is_edit": True, "type": "char"},
                    "type": {"value": {"id":field.ttype,"name":field.ttype.capitalize()}, "is_edit": False, "type": "char"},
                    "length": {"value": 0, "is_edit": True, "type": "char"},
                    "limits": {"value": {'is_limit':'NA' if field.limit_min == 0 and field.limit_max == 0 else 'set', "limit_min":field.limit_min, "limit_max":field.limit_max}, "is_edit": True, "type": "char"},
                    "format": {"value": {"id":field.date_format,"name":field.date_format.upper()} if field.date_format else 'NA', "is_edit": True, "type": "char"}
                }
                requested_data.append(table_vals)
            return _success_200('Table Fields Data Fetch Successfully !', requested_data)
        except Exception as e:
            return _error_400('Failed: ' + str(e))

    def _get_field_with_labels(self, model_id):
        cr = request.env.cr
        mg = tuple(['__last_update', 'display_name'])
        cr.execute(f"SELECT id, name, field_description, ttype, relation, relation_field, relation_table, column1, column2 FROM ir_model_fields WHERE model_id={model_id} AND name NOT IN {mg}")
        field_data = cr.fetchall()
        result = [dict(zip(['id', 'name', 'field_description', 'ttype', 'relation', 'relation_field', 'relation_table', 'column1', 'column2'], fd)) for fd in field_data]
        return result

    @http.route('/api/get_model_attributes', methods=["GET"], auth='none')
    def model_attributes(self, **kwargs):
        try:
            data = request.params.copy()
            table_id = data.get('table_id')
            result = {}
            if not table_id:
                return Response(json.dumps({"result": "Table ID not found."}), status=200,
                    headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                    content_type="application/json")
            query_model_name = f"SELECT model FROM ir_model WHERE id = {table_id} and from_api = True;"
            query_obj = request.env.cr
            query_obj.execute(query_model_name)
            model_obj = query_obj.fetchone()
            if not model_obj:
                return Response(json.dumps({"result": "Table does not exist or may not be custom table !"}),
                    status=200,
                    headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                    content_type="application/json")
            model_obj = model_obj[0]
            model_name = model_obj.replace('.', '_')
            header = {'id':'ID'}
            fields_data = self._get_field_with_labels(table_id)
            fields_data_names = {obj.get('name'):obj.get('name')[2:] for obj in fields_data if 'x_' in obj.get('name')}
            header.update({fields_data_names.get(obj.get('name')): obj.get('field_description') for obj in fields_data if fields_data_names.get(obj.get('name'))})
            header.update({obj.get('name'): obj.get('field_description') for obj in fields_data if not fields_data_names.get(obj.get('name'))})
            query_field = ','.join(obj.get('name') for obj in fields_data if obj.get('ttype') not in ['one2many', 'many2many'])+',id'
            relational_field = [obj for obj in fields_data if obj.get('ttype') in ['many2one','one2many', 'many2many']]
            if 'active' in header.keys():
                query_model_obj = f"SELECT {query_field} FROM {model_name} WHERE active = True;"
                query_obj.execute(query_model_obj)
                table_data = query_obj.dictfetchall()
            else:
                query_obj.rollback()
                query_model_obj = f"SELECT {query_field} FROM {model_name};"
                query_obj.execute(query_model_obj)
                table_data = query_obj.dictfetchall()
            table_data_new = []
            for td_dic in table_data:
                td_new_dic = {}
                for nk,nv in td_dic.items():
                    if fields_data_names.get(nk):
                        td_new_dic[fields_data_names[nk]] = nv
                    else:
                        td_new_dic[nk] = nv
                table_data_new.append(td_new_dic)
            res = {}
            for d in table_data:
                res[d.get('id')] = d.get('x_name') or d.get('name') or d.get("id")
            for obj in relational_field:
                relation_table = request.env['ir.model'].sudo().search([('model', '=', obj.get('relation'))],limit=1)
                search_field = 'id'
                for fls in ['x_name', 'name']:
                    if fls in relation_table.field_id.mapped('name'):
                        search_field = fls
                        break
                if obj.get('ttype') == 'many2many':
                    m2m_query = f"SELECT lb.* FROM   {obj.get('relation_table')} lb WHERE  EXISTS (SELECT FROM {model_name} l) ORDER  BY lb.{obj.get('column1')};"
                    query_obj.execute(m2m_query)
                    m2m_data = query_obj.fetchall()
                    m2m_ids = {}
                    for md in m2m_data:
                        m2m_ids[md[0]] = m2m_ids[md[0]]+[md[1]] if m2m_ids.get(md[0]) else [md[1]]
                    for k,v in m2m_ids.items():
                        m2m_ids[k] = [res.get(value) for value in v]
                    for td in table_data_new:
                        td[fields_data_names.get(obj.get('name'))] = m2m_ids.get(td.get('id')) if td.get('id') and m2m_ids.get(td.get('id')) else ""
                elif obj.get('ttype') == 'one2many':
                    o2m_query = f"SELECT {obj.get('relation_field')}, {search_field} FROM {obj.get('relation')};"
                    query_obj.execute(o2m_query)
                    o2m_data = query_obj.fetchall()
                    o2m_ids = {}
                    for md in o2m_data:
                        o2m_ids[md[0]] = o2m_ids[md[0]]+[md[1]] if o2m_ids.get(md[0]) else [md[1]]
                    for td in table_data_new:
                        td[fields_data_names.get(obj.get('name'))] = o2m_ids.get(td.get('id')) if td.get('id') and o2m_ids.get(td.get('id')) else ""
                elif obj.get('ttype') == 'many2one':
                    m2o_data = {}
                    for m2o_id in table_data:
                        if m2o_id.get(obj.get('name')):
                            m2o_ids = request.env[obj.get('relation')].sudo().browse(m2o_id.get(obj.get('name')))
                            m2o_data[m2o_id.get('id')] = m2o_ids.mapped(search_field)
                    for td in table_data_new:
                        if fields_data_names.get(obj.get('name')):
                            td[fields_data_names.get(obj.get('name'))] = m2o_data.get(td.get('id'))[0] if m2o_data.get(td.get('id')) and m2o_data.get(td.get('id'))[0] else ""
                else:
                    for td in table_data_new:
                        for td_key, td_val in td.items():
                            td[td_key] = td_val if td_val else ""
            result["total_record"] = len(table_data_new)
            result['header'] = header
            result['rows'] = table_data_new
            return Response(json.dumps({"result": result}, default=str), status=200,
                headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                content_type="application/json")
        except Exception as e:
            return Response(json.dumps({"Failed": str(e)}), status=200,
                            headers={"Content-Type": "application/json",
                                    "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")

    @http.route('/api/search_product_catalog', methods=["POST"], auth='none', type='json')
    def search_product_catalog(self, **kwargs):
        """Used to search keywords in given attributes and table"""
        try:
            data = request.jsonrequest
            search_keyword = data.get('search_keyword')
            result = []
            searched_records = 0
            total_records = 0
            if not search_keyword and data.get('search_in'):
                return _success_organization_error_200('Invalid Request, Search Keyword & Search In Required!!', [])
            for rec in data.get('search_in'):
                if not rec.get('table_id') and rec.get('search_attributes'):
                    return _success_organization_error_200('Table ID and Search Attributes Required!! ', [])
                table_exist = request.env['ir.model'].sudo().browse(rec.get('table_id')).exists()
                if not table_exist:
                    return _success_organization_error_200(f"Table ID '{rec.get('table_id')}' does not exists!!", [])

                field_query = []
                res = []
                table_name = table_exist.model
                table_obj = request.env[table_name].sudo()
                if any(sa for sa in rec.get('search_attributes') if sa not in table_exist.field_id.mapped('name')):
                    return _success_organization_error_200("Search attribute does not exist in table!!", [])
                search_attributes = table_exist.field_id.filtered(lambda x: x.name in rec.get('search_attributes'))
                for attribute in search_attributes:
                    domain = []
                    if attribute.ttype in ['date', 'datetime']:
                        if '/' in str(search_keyword):
                            domain += [(attribute.name, '=', search_keyword)]
                    elif attribute.ttype in ['integer', 'float', 'monetary']:
                        if str(search_keyword).isnumeric() or (
                                '.' in str(search_keyword) and str(search_keyword).replace('.', '', 1).isdigit()):
                            domain += [(attribute.name, '=', search_keyword)]
                    elif attribute.ttype == 'selection':
                        attribute_values = list(dict(table_obj._fields[attribute.name].selection).values())
                        domain += [(attribute.name, '=', search_keyword)]
                    elif attribute.ttype == 'boolean':
                        val = True if search_keyword.lower() == 'true' else False
                        domain += [(attribute.name, '=', val)]
                    elif attribute.ttype in ['char', 'text', 'html']:
                        if data.get('case_insensitive'):
                            domain += [(attribute.name, '=ilike', str(search_keyword))]
                        elif data.get('exact_match'):
                            domain += [(attribute.name, '=', str(search_keyword))]
                        else:
                            domain += [(attribute.name, 'ilike', '%' + str(search_keyword) + '%')]
                    elif attribute.ttype == 'many2one':
                        source_id = request.env[attribute.relation].sudo().search([('name', '=', search_keyword)])
                        if source_id:
                            domain += [(attribute.name, '=', source_id.id)]
                    if domain:
                        field_query += table_obj.search_read(domain, [attribute.name])
                    temp = []
                    for d in field_query:
                        for item in temp:
                            if d.get("id") == item.get("id"):
                                item.update(d)
                                break
                        else:
                            temp.append(d)
                table_data = []
                for row in temp:
                    table_data += [{'table_id': table_exist.id, 'table_name': table_exist.name, 'row_id': row['id'], 'data': row}]
                    del row['id']
                searched_records += len(temp)
                total_records += table_obj.search_count([])
                result += table_data
            return _success_200('Data Fetch Successfully !', {"searched_records": searched_records,
                                                              "total_records": total_records, 'result': result})
        except Exception as e:
            return _error_400("Failed :" + str(e))
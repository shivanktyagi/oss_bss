# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json
import base64
import odoo
from odoo import http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request, Response

class CrmLeadTasks(http.Controller):

    @http.route(['/api/crm/lead/sidepanels'], methods=["GET"], auth='none')
    def crm_lead_all_sidepanels(self, sidepanel_id=False, **kwargs):
        try:
            res = request.env['crm.lead.sidepanel'].sudo().search([('parent_id','=',False)])
            sidepanels = []
            for i in res:
                sidepanels.append({'id':i.id, 'name':i.name if i.name else '', 'child_ids': [{'id':ch.id, 'name': ch.name if ch.name else '', 'icon': ch.icon if ch.icon else ''} for ch in i.child_ids]})
            return Response(json.dumps(sidepanels), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")
        except AccessError:
            return None, 403
        except MissingError:
            return None, 404

    @http.route(['/api/crm/lead/headers', '/api/crm/lead/headers/<int:sidepanel_id>'], methods=["GET"], auth='none')
    def crm_lead_all_headers(self, sidepanel_id=False, **kwargs):
        try:
            if sidepanel_id:
                sd_id = request.env['crm.lead.sidepanel'].sudo().browse(int(sidepanel_id)).exists()
                if not sd_id:
                    return {
                        'success': False,
                        'status': 'Bad Request.',
                        'code': 400,
                        'response': 'lead Id Not Found'
                    }
                else:
                    res = sd_id.header_ids
            else:
                res = request.env['crm.lead.header'].sudo().search([])
            headers = []
            for i in res:
                headers.append({'id': i.id, 'name':i.name if i.name else '', 'icon': base64.b64encode(i.icon).decode('utf-8') if i.icon else ''})
            return Response(json.dumps(headers), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")
        except AccessError:
            return None, 403
        except MissingError:
            return None, 404

    def _get_task_data(self, tasks):
        result = []
        for i in tasks:
            res = {}
            res['task_id'] = i.task_id if i.task_id else ""
            res['name'] = i.name if i.name else ""
            res['due_date'] = i.due_date.strftime('%Y-%m-%d %H:%M') if i.due_date else ""
            res['assigned_to'] = i.assigned_to.name if i.assigned_to else ""
            res['assigned_by'] = i.assigned_by.name if i.assigned_by else ""
            res['state'] = i.state if i.state else ""
            res['lead_id'] = i.lead_id.name if i.lead_id else ""
            result.append(res)
        return result

    @http.route(['/api/crm/lead/tasks/', '/api/crm/lead/tasks/<int:lead_id>'], methods=["GET"], auth='none')
    def crm_lead_all_tasks(self, lead_id=False, **kwargs):
        try:
            domain = []
            if lead_id:
                lead_obj = request.env['crm.lead'].sudo().browse(lead_id).exists()
                if lead_obj:
                    domain += [('lead_id','=',lead_id),('task_type','=',lead_obj.type)]
            tasks = request.env['crm.lead.tasks'].sudo().search(domain)
            return Response(json.dumps({'Tasks': self._get_task_data(tasks)}), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")
        except AccessError:
            return None, 403
        except MissingError:
            return None, 404

    @http.route(['/api/crm/lead/tasks/create/'], methods=["POST"], auth='none')
    def crm_lead_task_create(self, **kwargs):
        vals = {}
        try:
            lead_id = kwargs.get('id')
            lead_t = request.env['crm.lead'].sudo().browse(int(lead_id)).exists()
            if not lead_id:
                result = {
                        'success': False,
                        'status': 'Bad Request.',
                        'code': 400,
                        'response': 'lead Id Not Found'
                    }
            else:
                vals['lead_id'] = int(lead_t)
            if kwargs.get('assigned_to'):
                assigned_to = request.env['res.users'].search([('name','=like',kwargs.get('assigned_to'))], limit=1).id
                if not assigned_to:
                    result = {
                        'success': False,
                        'status': 'Bad Request.',
                        'code': 400,
                        'response': 'Assigned To User Not Found'
                    }
                else:
                    vals['assigned_to'] = assigned_to
            if kwargs.get('assigned_by'):
                assigned_by = request.env['res.users'].search([('name','=like',kwargs.get('assigned_by'))], limit=1).id
                if not assigned_by:
                    result = {
                        'success': False,
                        'status': 'Bad Request.',
                        'code': 400,
                        'response': 'Assigned By User Not Found'
                    }
                else:
                    vals['assigned_by'] = assigned_by

            vals['name'] = kwargs.get('name', False)
            vals['due_date'] = kwargs.get('due_date', False)
            task_id = request.env['crm.lead.tasks'].sudo().create(vals)
            if task_id:
                result = {
                        'success': True,
                        'status': 'Bad Request.',
                        'code': 200,
                        'response': 'Task Created Successfully!!'
                    }
            else:
                result = {
                        'success': False,
                        'status': 'Bad Request.',
                        'code': 400,
                        'response': 'Task Creation Fail!!'
                    }
            return Response(json.dumps(result),headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")
        except AccessError:
            return None, 403
        except MissingError:
            return None, 404


    @http.route(['/api/crm/lead/stakeholders', '/api/crm/lead/stakeholders/<int:lead_id>'], methods=["GET"], auth='none')
    def crm_lead_all_stakeholders(self, lead_id=False, **kwargs):
        try:
            domain = []
            if lead_id:
                domain += [('lead_id','=',lead_id)]
            stakeholders = request.env['crm.lead.stakeholders'].sudo().search(domain)
            result = {}
            for i in stakeholders:
                result[i.name] = base64.b64encode(i.photo).decode('utf-8') if i.photo else False
            return Response(json.dumps(result), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")
        except AccessError:
            return None, 403
        except MissingError:
            return None, 404


    @http.route(['/api/crm/lead/stakeholders/create/<int:lead_id>'], methods=["GET"], auth='none')
    def crm_lead_stakeholder_create(self, lead_id, **kwargs):
        vals = {}
        try:
            if not lead_id:
                result = {
                        'success': False,
                        'status': 'Bad Request.',
                        'code': 400,
                        'response': 'Lead ID is required for creating Stakeholder.'
                    }
            else:
                vals['lead_id'] = int(lead_id)
            vals['name'] = kwargs.get('name', False)
            vals['photo'] = kwargs.get('photo', False)
            stakeholder_id = request.env['crm.lead.stakeholders'].sudo().create(vals)
            if stakeholder_id:
                result = {
                        'success': True,
                        'status': 'Success.',
                        'code': 200,
                        'response': 'Stakeholder Created Successfully!!'
                    }
            else:
                result = {
                        'success': False,
                        'status': 'Bad Request.',
                        'code': 400,
                        'response': 'Stakeholder Not Created!!'
                    }
            return Response(json.dumps(result), headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")
        except AccessError:
            return None, 403
        except MissingError:
            return None, 404
    

    @http.route('/api/get/customers/<string:type>', methods=["GET"], auth="none")
    def receive_json(self, type, **args):
        domain = []
        if type == 'contact':
            domain = [('opportunity_ids','!=', False),('sale_order_ids','!=', False),('active','=',True)]
        elif type == 'accounts':
            domain = [('sale_order_ids','!=', False),('active','=',True)]
        else:
            return {
                    'success': False,
                    'status': 'Bad Request.',
                    'code': 400,
                    'response': 'Invalid type value!!'
                }
        records = request.env['res.partner'].sudo().search(domain)
        data = []
        for record in records:
            meeting_data = []
            tags = []
            contact_address = []
            invoicing = []
            sale_orders = []
            opportunities = []
            invoiced_list = []
            total_amount = 0
            sales_purchase = {
                "sales": {
                    "sales_team": record.team_id.name if record.team_id and record.team_id.name else '',
                    "salesperson": record.user_id.name if record.user_id and record.user_id.name else '',
                    # "payment_terms": {'id': record.property_payment_term_id.id, 'name': record.property_payment_term_id.name},
                    # "pricelist": {'id': record.property_product_pricelist.id, 'name': record.property_product_pricelist.name}
                },
                "fiscal_information": {
                    # "property_account_position_id": {'id': record.property_account_position_id.id, 'name': record.property_account_position_id.name},
                },
                "inventory": {
                    # "customer_location": record.property_stock_customer,
                    # "vendor_location": record.property_stock_supplier
                },
                "purchase": {
                    # "payment_terms": record.property_supplier_payment_term_id
                },
                "misc": {
                    "reference": record.ref if record.ref else '',
                    # "website": record.website_id.name,
                    "industry": record.industry_id.name if record.industry_id and record.industry_id.name else ''
                }
            }
            for invoice in record.invoice_ids:
                invoiced_list.append(
                    {"id": invoice.id, "invoice_number": invoice.name if invoice.name else '', "amount": invoice.amount_untaxed if invoice.amount_untaxed else ''})
                total_amount += invoice.amount_untaxed
            for opportunity in record.opportunity_ids:
                opportunities.append({"id": opportunity.id, "name": opportunity.name if opportunity.name else ''})
            for order in record.sale_order_ids:
                sale_orders.append({"id": order.id, "order_id": order.name if order.name else ''})
            for banks_account in record.bank_ids:
                invoicing.append({"bank_name": banks_account.bank_id.name if banks_account.bank_id and banks_account.bank_id.name else '', "account_number": banks_account.acc_number if banks_account.acc_number else ''})
            for address in record.child_ids:
                contact_address.append({
                    "id": address.id if address.id else '',
                    "type": address.type if address.type else '',
                    "name": address.name if address.name else '',
                    "phone": address.phone if address.phone else '',
                    "email": address.email if address.email else '',
                    "mobile": address.mobile if address.mobile else '',
                    "street": address.street if address.street else '',
                    "street2": address.street2 if address.street2 else '',
                    "zip": address.zip if address.zip else '',
                    "city": address.city if address.city else '',
                    "state": address.state_id.name if address.state_id.name else '',
                    "country": address.country_id.name if address.country_id and address.country_id.name else '',
                    "notes": address.comment if address.comment else ''
                })
            for category in record.category_id:
                tags.append({"id": category.id if category.id else '', "name": category.name if category.name else ''})
            if record.meeting_count > 0:
                for meetings_info in record.meeting_ids:
                    meeting_data.append(
                        {
                            "id": meetings_info.id if meetings_info.id else '',
                            "name": meetings_info.name if meetings_info.name else '',
                            "partner_ids": meetings_info.partner_ids,
                            "start": meetings_info.start if meetings_info.start else '',
                            "end": meetings_info.stop if meetings_info.stop else '',
                            "duration": meetings_info.duration if meetings_info.duration else '',
                            "allday": meetings_info.allday if meetings_info.allday else '',
                            "organizer": meetings_info.user_id.name if meetings_info.user_id.name else '',
                            "description": meetings_info.description if meetings_info.description else ''
                        })
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            image_url = base_url + '/web/image?' + 'model=res.partner&id=' + str(record.id) + '&field=image_128'
            result = {
                "id": record.id if record.id else '',
                "title": record.title.name if record.title and record.title.name else '',
                "name": record.name if record.name else '',
                "job_position": record.function if record.function else '',
                "image": image_url if image_url else '',
                "company_type": record.company_type if record.company_type else '',
                "street": record.street if record.street else '',
                "street2": record.street2 if record.street2 else '',
                "zip": record.zip if record.zip else '',
                "city": record.city if record.city else '',
                "state": record.state_id.name if record.state_id.name else '',
                "country": record.country_id.name if record.country_id and record.country_id.name else '',
                # "gst_treatment": record.l10n_in_gst_treatment,
                "vat": record.vat if record.vat else '',
                "tags": tags,
                "phone": record.phone if record.phone else '',
                "email": record.email if record.email else '',
                "mobile": record.mobile if record.mobile else '',
                "website": record.website if record.website else '',
                "meetings": record.meeting_count if record.meeting_count else '',
                "meeting_info": meeting_data,
                "sale_order_count": record.sale_order_count,
                "sale_orders": sale_orders,
                "opportunities_count": record.opportunity_count,
                "opportunities": opportunities,
                "total_invoiced": total_amount,
                "invoiced_lines": invoiced_list,
                "contact_address": contact_address,
                "sales_purchase": sales_purchase,
                "invoicing": invoicing,
                "internal_notes": record.comment if record.comment else ''
            }
            data.append(result)
        if data:
            res = {
                "success": True,
                "total_count": len(records),
                "result": data
            }
            return Response(
                json.dumps(res, default=str),
                status=200,
                mimetype='application/json'
            )
        else:
            headers = {'Content-Type': 'application/json'}
            body = {"success": False, "status": "No Data Found!!!", "code": 200, "total_count": 0, "result": []}
            return Response(json.dumps(body), headers=headers)


# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json
import xlrd
import base64
import odoo
from odoo import http, _
from odoo.http import request, Response
import bs4
from odoo.addons.oss_contact.controllers.contact_creation import _success_organization_200, _success_organization_error_200, _success_200

Org_Contact_Header = {"name":"First Name",
        "spoc_lname": "Last Name",
        "email": "Email",
        "email_enable": "Email Enable",
        "phone_code": "Phone Code",
        "phone": "Phone",
        "phone_enable": "Phone Enable",
        "preferred_type": "Preferred Type",
        "other_medium_1": "Other Medium 1",
        "other_phone_code1": "Other Phone Code 1",
        "other_details_1": "Other Details 1",
        "prefer_other_detail_1": "Prefer Other Detail 1",
        "enable_other_1": "Enable Other 1",
        "other_medium_2": "Other Medium 2",
        "other_phone_code2": "Other Phone Code 2",
        "other_details_2": "Other Details 2",
        "prefer_other_detail_2": "Prefer Other Detail 2",
        "enable_other_2": "Enable Other 2",
        "spoc_role": "Role",
        "role_details": "Role Details",
        "other_role": "Other Role",
        "designation": "Additional Role",
        "comment": "Remarks",
        }

class CreateOrganisation(http.Controller):
    @http.route('/api/org_medium/dropdown', methods=["GET"], auth="none")
    def org_medium_dropdown(self, **kwargs):
        try:
            requested_data = []
            medium_obj = request.env['utm.medium'].sudo().search([])
            for medium_id in medium_obj:
                vals = {'id': medium_id.id, 'name': medium_id.name if medium_id.name else ''}
                requested_data.append(vals)
            return Response(json.dumps(requested_data), status=200,
                            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")
        except Exception as e:
            return Response(json.dumps({'message': 'Failed!!', 'reason': str(e)}), status=400,
                            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")

    @http.route('/api/organisation/dropdown', methods=["GET"], auth="none")
    def organisation_dropdown(self, **kwargs):
        try:
            requested_data = []
            org_ids = request.env['res.partner'].sudo().search([('is_organisation','=',True)])
            for org in org_ids:
                vals = {'id': org.id, 'name': org.name if org.name else ''}
                requested_data.append(vals)
            return Response(json.dumps(requested_data), status=200,
                            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")
        except Exception as e:
            return Response(json.dumps({'message': 'Failed!!', 'reason': str(e)}), status=400,
                            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")

    @http.route('/api/organisation/roles_details/dropdown', methods=["GET"], auth="none")
    def organisation_sites_dropdown(self, **kwargs):
        try:
            params = request.params
            org_id = False
            if params.get('organisation_id') and params.get('organisation_id').isdigit():
                org_id = int(params.get('organisation_id'))
            if params.get('role') and org_id:
                org = request.env['res.partner'].sudo().browse(org_id).exists()
                result = []
                if params.get('role') == '2':
                    account_ids = org.bank_ids if org else request.env['res.partner.bank'].sudo().search([])
                    result = [{'id': account.id, 'name': account.acc_holder_name if account.acc_holder_name else ''} for account in account_ids if account.acc_holder_name]
                elif params.get('role') == '3':
                    site_ids = request.env['res.partner'].sudo().search([('is_site','=',True),('organisation_id','=',org.id)])
                    result = [{'id': site.id, 'name': site.name_of_site if site.name_of_site else ''} for site in site_ids if site.name_of_site]
                else:
                    result = []
                return Response(json.dumps(result), status=200,
                        headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                        content_type="application/json")
            else:
                return Response(json.dumps({'message': 'Invalid Request Payload'}), status=200,
                        headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                        content_type="application/json")
        except Exception as e:
            return Response(json.dumps({'message': 'Failed!!', 'reason': str(e)}), status=400,
                            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")

    @http.route('/api/organisation/roles/dropdown', methods=["GET"], auth="none")
    def organisation_roles_dropdown(self, **kwargs):
        try:
            roles = [{'id':int(obj[0]), 'name':obj[1]} for obj in request.env['res.partner'].sudo()._fields["spoc_role"].selection]
            return Response(json.dumps(roles), status=200,
                            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")
        except Exception as e:
            return Response(json.dumps({'message': 'Failed!!', 'reason': str(e)}), status=400,
                            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")

    def _get_contact_table_info(self, contact_id):
        last_name = " " +contact_id.spoc_lname if contact_id.spoc_lname else ""
        other_details = False
        preferred_contact_medium = False
        if contact_id.preferred_type and contact_id.preferred_type.lower() == 'email':
            preferred_contact_medium = 'Email'
        elif contact_id.preferred_type and contact_id.preferred_type.lower() == 'phone':
            preferred_contact_medium = 'Phone'
        else:
            preferred_contact_medium = False
        if contact_id.other_detail_ids:
            other_details = [{"id": cd.medium_id.id,
                            "name":cd.medium_name,
                            "details": cd.medium_detail,
                            "phone_code": cd.phone_code if cd.medium_name and cd.medium_name.lower() == 'phone' else '',
                            "enable": cd.enable,
                            "is_preferred": cd.is_preferred_contact} for cd in contact_id.other_detail_ids]
        remarks = False
        role_details = []
        if contact_id.comment:
            remarks = bs4.BeautifulSoup(contact_id.comment,features="lxml")
        if contact_id.spoc_role == '2':
            account_ids = request.env['res.partner.bank'].sudo().search([('bank_spoc_id','=',contact_id.id)])
            role_details = [{'id': account.id, 'name': account.acc_holder_name if account.acc_holder_name else ''} for account in account_ids if account.acc_holder_name]
        if contact_id.spoc_role == '3':
            site_ids = request.env['res.partner'].sudo().search([('email','=',contact_id.email),('mobile','=',contact_id.phone)])
            role_details = [{'id': site.id, 'name': site.name_of_site if site.name_of_site else ''} for site in site_ids if site.name_of_site]
        spoc_role = False
        if contact_id.spoc_role:
            spoc_role_id = dict(request.env['res.partner'].sudo()._fields["spoc_role"].selection)
            spoc_role_key = list(spoc_role_id.keys())[list(spoc_role_id.keys()).index(contact_id.spoc_role)]
            spoc_role_value = spoc_role_id[contact_id.spoc_role]
            spoc_role = {'id':spoc_role_key, 'name':spoc_role_value}
        vals = {
            "contact_id": contact_id.id,
            "first_name": contact_id.name if contact_id.name else "",
            "last_name": contact_id.spoc_lname if contact_id.spoc_lname else "",
            "name": contact_id.name + last_name if contact_id.name or last_name else "",
            "organisation_name": contact_id.organisation_id.name if contact_id.organisation_id and contact_id.organisation_id.name else "",
            "organisation_id": contact_id.organisation_id.id if contact_id.organisation_id else "",
            "email": contact_id.email if contact_id.email else "",
            "email_enable": contact_id.email_enable,
            "phone_code": contact_id.phone_code if contact_id.phone_code else "",
            "phone": contact_id.phone if contact_id.phone else "",
            "phone_enable": contact_id.phone_enable,
            "preferred_type": preferred_contact_medium if preferred_contact_medium else "",
            "role": spoc_role if contact_id.spoc_role else "",
            "other_role": contact_id.other_role if contact_id.other_role else "",
            "additional_role": contact_id.designation if contact_id.designation else "",
            "other_details": other_details if other_details else [],
            "remarks": remarks.get_text() if remarks else "",
            "image": base64.b64encode(contact_id.image_1920).decode('utf-8') if contact_id.image_1920 else '',
            "added_on": contact_id.create_date.strftime('%d %b %Y') if contact_id.create_date else '',
            "updated_on": contact_id.write_date.strftime('%d %b %Y') if contact_id.write_date else '',
        }
        return vals

    @http.route('/api/get_all_contact_list', methods=["GET"], auth="none")
    def get_all_contact_list(self, **kw):
        try:
            params = request.params
            contact_obj = request.env['res.partner'].sudo()
            domain = [('is_org_contact','=',True)]
            if params.get('search_filter'):
                domain += ['|',('name','ilike','%'+params.get('search_filter')+'%'),('spoc_lname','ilike','%'+params.get('search_filter')+'%')]
            limit = None
            offset = None
            if params.get('organisation_id') and params.get('organisation_id').isdigit():
                domain += [('organisation_id','=',int(params.get('organisation_id')))]
            contact_count = contact_obj.search_count(domain)
            if params.get('max_page') and params.get('max_page').isdigit() and params.get('min_page') and params.get('min_page').isdigit():
                limit = int(params.get('max_page')) - int(params.get('min_page'))
                offset = int(params.get('min_page'))
            contact_ids = contact_obj.search(domain, order='id desc', limit=limit, offset=offset)
            contact_list = []
            if not contact_ids:
                return Response(json.dumps({"total_record": contact_count, 'data': contact_list}), status = 200,
                            headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,
                            content_type = "application/json")
            header = {"organisation_name":"Organisation","name": "Name","other_role": "Role", "email":"Email", "phone":"Phone"}
            for contact_id in contact_ids:
                vals = self._get_contact_table_info(contact_id)
                del vals['first_name']
                del vals['last_name']
                contact_list.append(vals)
            return Response(json.dumps({"total_record": contact_count, 'header': header, 'data': contact_list}), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")
        except Exception as e:
            vals = {
                'success': False,
                'status': 'Failed Due To: ' + str(e),
                'code': 404,
            }
            return Response(json.dumps(vals), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")


    @http.route('/api/get_contact_info', methods=["GET"], auth="none")
    def get_contact_info(self, **kw):
        try:
            params = request.params
            contact_obj = request.env['res.partner'].sudo()
            domain = [('is_org_contact','=',True)]
            if not params.get('organisation_id') or not params.get('contact_id'):
                return Response(json.dumps("Invalid Request Payload"), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")
            if params.get('organisation_id') and params.get('organisation_id').isdigit():
                domain += [('organisation_id','=',int(params.get('organisation_id')))]
            if params.get('contact_id') and params.get('organisation_id').isdigit():
                domain += [('id','=',int(params.get('contact_id')))]
            contact_id = contact_obj.search(domain, order='id desc', limit=1)
            if not contact_id:
                return Response(json.dumps({"message":"Contact Not Found"}), status = 200,
                            headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,
                            content_type = "application/json")
            vals = self._get_contact_table_info(contact_id)
            del vals['name']
            return Response(json.dumps(vals), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")
        except Exception as e:
            vals = {
                'success': False,
                'status': 'Failed Due To: ' + str(e),
                'code': 404,
            }
            return Response(json.dumps(vals), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")


    @http.route('/api/create_organisation', auth='public', csrf=False, type='json', methods=['POST'])
    def api_create_organisation(self, **kwargs):
        try:
            data = request.jsonrequest
            if not (data.get('organisation_name') and data.get('registration_no') and \
            data.get('organisation_address').get('address_1') and \
            data.get('organisation_address').get('pin_code') and \
            data.get('organisation_address').get('city') and \
            data.get('organisation_address').get('state_id') and \
            data.get('organisation_address').get('country_id') and \
            data.get('billing_address').get('address_1') and \
            data.get('billing_address').get('pin_code') and
            data.get('billing_address').get('city') and \
            data.get('billing_address').get('state_id') and \
            data.get('billing_address').get('country_id') and \
            data.get('phone_code') and data.get('spoc_phone') and \
            data.get('spoc_first_name') and data.get('spoc_email')):
                return _success_organization_error_200('Invalid Request!!',{})
            res_partner_obj = request.env['res.partner'].sudo()
            res_bank_obj = request.env['res.bank'].sudo()
            org_bank_ids = []
            # validation for relational fields
            if data.get('parent_organisation_id'):
                is_valid_parent_org = res_partner_obj.search(
                    [('id', '=', data.get('parent_organisation_id'))]).exists()
                if not is_valid_parent_org:
                    return _success_organization_error_200('Parent Organisation ID Does Not Exists!!',{})
            if data.get('industry_id'):
                is_valid_industry = request.env['res.partner.industry'].sudo().search(
                    [('id', '=', data.get('industry_id'))]).exists()
                if not is_valid_industry:
                    return _success_organization_error_200('Industry ID Does Not Exists!!',{})
            is_valid_country_id = request.env['res.country'].sudo().search(
                [('id', 'in', [data.get('organisation_address').get('country_id'),data.get('billing_address').get('country_id')])])
            if not is_valid_country_id:
                return _success_organization_error_200('Country ID For Organisation Address or Billing Addresss Does Not Exists!!',{})
            is_valid_state_id = request.env['res.country.state'].sudo().search(
                [('id', 'in', [data.get('organisation_address').get('state_id'),data.get('billing_address').get('state_id')])]).exists()
            if not is_valid_state_id:
                return _success_organization_error_200("State ID For Organisation Address or Billing Addresss Does Not Exists!!",{})
            organisation_vals = {
                "name": data.get('organisation_name'),
                "street": data.get('organisation_address').get('address_1'),
                "street2": data.get('organisation_address').get('address_2') if data.get('organisation_address').get('address_2') else False,
                "zip": data.get('organisation_address').get('pin_code'),
                "city": data.get('organisation_address').get('city'),
                "state_id": data.get('organisation_address').get('state_id'),
                "country_id": data.get('organisation_address').get('country_id'),
                "registration_no": data.get('registration_no'),
                "industry_id": data.get('industry_id') if data.get('industry_id') else False,
                "comment": data.get('description') if data.get('description') else False,
                "parent_organisation_id": data.get('parent_organisation_id') if data.get('parent_organisation_id') else False,
                "invoice_address_1": data.get('billing_address').get('address_1'),
                "invoice_address_2": data.get('billing_address').get('address_2') if data.get('billing_address').get('address_2') else False,
                "invoice_zip": data.get('billing_address').get('pin_code'),
                "invoice_city": data.get('billing_address').get('city'),
                "invoice_state_id": data.get('billing_address').get('state_id'),
                "invoice_country_id": data.get('billing_address').get('country_id'),
                "is_organisation": True
            }
            org_spoc_id = res_partner_obj.search(['|',('mobile', '=', data.get('spoc_phone')), ('email', '=', data.get('spoc_email'))], limit=1)
            if not org_spoc_id:
                spoc_vals = {
                    "name": data.get("spoc_first_name"),
                    "spoc_lname": data.get("spoc_last_name"),
                    "email": data.get("spoc_email"),
                    "phone": data.get("spoc_phone"),
                    "is_org_contact": True,
                    "phone_code": data.get("phone_code")
                }
                org_spoc_id = res_partner_obj.create(spoc_vals)
            org_acc_no = [anum.get('account_number') for anum in data.get('account_details')]
            if request.env['res.partner.bank'].sudo().search([('sanitized_acc_number','in',org_acc_no)]):
                return _success_organization_error_200("Account Number Already Exist! :",{})
            for rec in data.get('account_details'):
                if not (rec.get('account_number') and rec.get('account_name') and rec.get('bank_name') and
                        rec.get('bank_first_name') and rec.get('bank_email') and rec.get('phone_code') and
                        rec.get('bank_phone')):
                    return _success_organization_error_200('Invalid Request!!',{})
                if rec.get('bank_address').get('state_id'):
                    is_valid_bank_state_id = request.env['res.country.state'].sudo().browse(rec.get('bank_address').get('state_id')).exists()
                    if not is_valid_bank_state_id:
                        return _success_organization_error_200("State ID For Bank Addresss Does Not Exists!!",{})
                if rec.get('bank_address').get('country_id'):
                    is_valid_bank_country_id = request.env['res.country'].sudo().browse(rec.get('bank_address').get('country_id')).exists()
                    if not is_valid_bank_country_id:
                        return _success_organization_error_200("Country ID For Bank Addresss Does Not Exists!!",{})
                bank_obj_rec = res_bank_obj.search([('name', '=', rec.get('bank_name'))], limit=1)
                if not bank_obj_rec:
                    bank_vals = {
                    "name": rec.get('bank_name'),
                    "street": rec.get('bank_address').get('address_1') if rec.get('bank_address').get(
                        'address_1') else '',
                    "street2": rec.get('bank_address').get('address_2') if rec.get('bank_address').get(
                        'address_2') else '',
                    "zip": rec.get('bank_address').get('pin_code') if rec.get('bank_address').get('pin_code') else '',
                    "city": rec.get('bank_address').get('city') if rec.get('bank_address').get('city') else '',
                    "state": rec.get('bank_address').get('state_id') if rec.get('bank_address').get('state_id') else '',
                    "country": rec.get('bank_address').get('country_id') if rec.get('bank_address').get(
                        'country_id') else '',
                    }
                    bank_obj_rec = res_bank_obj.create(bank_vals)
                spoc_obj_rec = res_partner_obj.search(['|',('mobile', '=', rec.get('bank_phone')), ('email', '=', rec.get('bank_email'))], limit=1)
                if not spoc_obj_rec:
                    spoc_vals={
                    "name": rec.get('bank_first_name'),
                    "spoc_lname": rec.get('bank_last_name') if rec.get('bank_last_name') else '',
                    "email": rec.get('bank_email'),
                    "phone_code": rec.get('phone_code'),
                    "phone": rec.get('bank_phone'),
                    "is_bank_spoc": True,
                    "is_org_contact": True,
                    }
                    spoc_obj_rec = res_partner_obj.create(spoc_vals)
                account_vals={
                    "acc_number": rec.get('account_number'),
                    "acc_holder_name": rec.get('account_name'),
                    "bank_id": bank_obj_rec.id,
                    "bank_spoc_id": spoc_obj_rec.id,
                    'partner_id': spoc_obj_rec.id
                }
                created_account_id = request.env['res.partner.bank'].sudo().create(account_vals)
                org_bank_ids.append(created_account_id.id)
            organisation_vals.update({'bank_ids': [(6, 0, org_bank_ids)], 'spoc_id':org_spoc_id.id})
            res = res_partner_obj.create(organisation_vals)
            org_spoc_id.organisation_id = res.id
            spoc_obj_rec.organisation_id = res.id
            return _success_organization_200("Organisation Successfully Created",{})
        except Exception as e:
            return _success_organization_error_200("Failed :" + str(e),{})

    @http.route('/api/organisation_generate_excel_file', csrf=False, methods=["GET"], auth='none')
    def organisation_generate_excel_file(self, **kwargs):
        try:
            header = list(Org_Contact_Header.values())
            return Response(json.dumps({'success': True, 'status': 'Success', 'header': header}), status=200,
                headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                content_type="application/json")
        except Exception as e:
            return Response(json.dumps({'success': False, 'status': 'Failed Due To: ' + str(e)}), status=200,
                            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")

    def _update_previous_spoc_details(self, role, other_role, contact):
        if contact.spoc_role in [1,'1'] and role not in [1,'1']:
            contact.organisation_id.spoc_id = False
        elif contact.spoc_role in [2,'2'] and role not in [2,'2']:
            accounts = contact.organisation_id.bank_ids.filtered(lambda obj: obj.bank_spoc_id.id == contact.id)
            accounts.sudo().write({'bank_spoc_id':False})
        elif contact.spoc_role in [3,'3'] and role not in [3,'3']:
            sites = request.env['res.partner'].sudo().search([('spoc_id', '=', contact.id), ('is_site', '=', True),('organisation_id','=',contact.organisation_id.id)])
            sites.sudo().write({
                    'spoc_lname': False,
                    'email': False,
                    'phone_code': False,
                    'mobile': False,
                    'spoc_id':False})
        else:
            contact.other_role = False

    def _create_spoc_details(self, role, role_details,other_role, contact):
        self._update_previous_spoc_details(role,other_role,contact)
        if role in [2, '2']:
            accounts = request.env['res.partner.bank'].sudo().browse(role_details).exists()
            if accounts:
                accounts.sudo().write({'bank_spoc_id': contact.id})
            contact.spoc_role = '2'
            contact.other_role = False
        elif role in [3,'3']:
            sites = request.env['res.partner'].sudo().search([('id', 'in', role_details), ('is_site', '=', True)])
            if sites:
                sites.sudo().write(
                    {'name': contact.name,
                    'spoc_lname': contact.spoc_lname if contact.spoc_lname else '',
                    'email': contact.email,
                    'phone_code': contact.phone_code,
                    'mobile': contact.phone,
                    'spoc_id': contact.id
                    })
            contact.spoc_role = '3'
            contact.other_role = False
        elif role == 1:
            contact.spoc_role = '1'
            contact.organisation_id.spoc_id = contact.id
            contact.other_role = False
        else:
            contact.other_role = other_role
            contact.spoc_role = '4'
    
    @http.route('/api/org_contact/create', auth='none', type="json", methods=['POST'])
    def org_contact_create(self, **kwargs):
        try:
            other_medium_ids = []
            data = request.jsonrequest
            if not (data.get('first_name') and data.get('role') and data.get('organisation_id') and
                    data.get('email') and data.get('phone')):
                return _success_organization_error_200('Invalid Request!!', {})
            org_obj = request.env['res.partner'].sudo().search(
                [('is_organisation', '=', True), ('id', '=', int(data.get('organisation_id')))], limit=1)
            if not org_obj:
                return _success_organization_error_200('Organisation ID does not exists!!', {})
            org_spoc_id = request.env['res.partner'].sudo().search(
                ['|', ('phone', '=', data.get('phone')), ('email', '=', data.get('email'))], limit=1)
            if org_spoc_id:
                return _success_organization_error_200("Contact Already Exists!!", {})
            if data.get('role') == 1 or data.get('role') == '1':
                org_contact_obj = request.env['res.partner'].sudo().search(
                    [('is_org_contact', '=', True), ('organisation_id', '=', org_obj.id),('spoc_role','=','1')])
                if org_contact_obj:
                    return _success_organization_error_200("Another Contact exist as Org SPOC for this organisation. Remove them as SPOC to set this contact as the New SPOC.", {})
            if data.get('preferred_type') and (data.get('other_details')):
                for rec in data.get('other_details'):
                    if rec.get('is_preferred_contact'):
                        return _success_organization_error_200("Only one communication type can be set as Preferred",{})
            vals = {
                'name': data.get('first_name'),
                'spoc_lname': data.get('last_name') if data.get('last_name') else False,
                'organisation_id': org_obj.id,
                'email': data.get('email'),
                "email_enable": data.get('email_enable') if data.get('email_enable') else False,
                'phone_code': data.get('phone_code') if data.get('phone_code') else False,
                'phone': data.get('phone'),
                "phone_enable": data.get('phone_enable') if data.get('phone_enable') else False,
                'preferred_type': data.get('preferred_type') if data.get('preferred_type') else False,
                'comment': data.get('remark') if data.get('remark') else False,
                'property_stock_customer': False,
                'property_stock_supplier': False,
                'is_org_contact': True,
                'designation': data.get('additional_role') if data.get('additional_role') else False
            }
            res_partner_obj = request.env['res.partner'].sudo().create(vals)
            self._create_spoc_details(data.get('role'),data.get('role_details'),data.get('other_role'),res_partner_obj)
            if data.get('other_details'):
                medium_id_obj = request.env['utm.medium'].sudo()
                for rec in data.get('other_details'):
                    rec['is_preferred_contact'] = rec.get('is_preferred_contact') if rec.get('is_preferred_contact') else False
                    rec['enable'] = rec.get('enable') if rec.get('enable') else False
                    other_details_phone_medium_id = medium_id_obj.browse(rec.get('medium_id')).exists()
                    if other_details_phone_medium_id and other_details_phone_medium_id.name.upper() != 'PHONE':
                        rec['phone_code'] = False
                    create_other_details = request.env['contact.other.detail'].sudo().create(rec)
                    other_medium_ids.append(create_other_details.id)
            res_partner_obj.other_detail_ids = [(6, 0, other_medium_ids)]
            return _success_organization_200("Contact Created Successfully !!", {'id': res_partner_obj.id})
        except Exception as e:
            return _success_organization_error_200("Failed :" + str(e), {})
    
    @http.route('/api/org_contact/update', type="json", methods=["POST"], auth="none")
    def update_contact(self, **kw):
        data = request.jsonrequest
        contact_id = data.get('contact_id')
        try:
            contact = request.env['res.partner'].sudo().search([('id', '=', contact_id), ('is_org_contact', '=', True)],limit=1)
            if not contact:
                return _success_organization_error_200("Contact Id Not Found", {})
            other_detail_ids = request.env['contact.other.detail'].sudo()
            if data.get('organisation_id') != contact.organisation_id.id:
                return _success_organization_error_200("Organisation ID cannot be Updated. ", {})
            if data.get('preferred_type') and (data.get('other_details')):
                for rec in data.get('other_details'):
                    if rec.get('is_preferred_contact'):
                        return _success_organization_error_200("Only one communication type can be set as Preferred", {})
            if data.get('other_details'):
                for cid in contact.other_detail_ids.ids:
                    contact.other_detail_ids = [(2,cid)]
                for rec in data.get('other_details'):
                    medium_id = request.env['utm.medium'].sudo().browse(rec.get('medium_id')).exists()
                    if not medium_id:
                        return _success_organization_error_200("Contact Other Details Id Not Exist ", {})
                    other_vals = {"medium_id": medium_id.id, "medium_detail": rec.get('medium_detail'), 
                    "is_preferred_contact": rec.get("is_preferred_contact"),'enable':rec.get('enable')}
                    if medium_id.name.lower() == 'phone':
                        other_vals['phone_code'] = rec.get('phone_code')
                    other_id = other_detail_ids.create(other_vals)
                    contact.other_detail_ids = [(4,other_id.id)]
            if data.get('role') == 'org_spoc' and contact.organisation_id.spoc_id.id != contact.id:
                return _success_organization_error_200("Another Contact exist as Org SPOC for this organisation. Remove them as SPOC to set this contact as the New SPOC.",{})
            try:
                vals = {
                    'name': data.get('first_name') if data.get('first_name') else contact.name,
                    'spoc_lname': data.get('last_name') if data.get('last_name') else contact.spoc_lname,
                    'organisation_id': data.get('organisation_id') if data.get(
                        'organisation_id') else contact.organisation_id,
                    'phone_code': data.get('phone_code') if data.get('phone_code') else contact.phone_code,
                    'phone': data.get('phone') if data.get('phone') else contact.phone,
                    "phone_enable": data.get('phone_enable') if data.get('phone_enable') else False,
                    'email': data.get('email') if data.get('email') else contact.email,
                    "email_enable": data.get('email_enable') if data.get('email_enable') else False,
                    "preferred_type": data.get('preferred_type'),
                    'comment': data.get('remarks') if data.get('remarks') else contact.comment,
                    'designation': data.get('additional_role')
                }
                contact.sudo().write(vals)
                self._create_spoc_details(data.get('role'),data.get('role_details'),data.get('other_role'),contact)
                return _success_organization_200('Contact Details Successfully Updated.', {})
            except Exception as e:
                return _success_organization_error_200("Contact Details Not Updated." + str(e), {})
        except Exception as e:
            return _success_organization_error_200("Invalid request payload. " + str(e), {})

    @http.route('/api/organisation_count', methods=["GET"], auth='none')
    def get_organisation_count(self, **kw):
        try:
            data = request.params.copy()
            results = []
            res_partner_obj = request.env['res.partner'].sudo()
            total_contacts = res_partner_obj.search_count([('is_org_contact', '=', True)])
            if data.get('organisation_name'):
                filtered_partner_obj = res_partner_obj.search(
                    [('is_organisation', '=', True), ('name', 'ilike', data.get('organisation_name'))])
            else:
                filtered_partner_obj = res_partner_obj.search([('is_organisation', '=', True), ('name', '!=', None)])
            if not filtered_partner_obj:
                return Response(json.dumps({'message': 'No Record Found!!', 'results': results}),
                                status=200,
                                headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                                content_type="application/json")
            for rec in filtered_partner_obj:
                vals = {}
                vals['organisation_id'] = rec.id
                vals['organisation_name'] = rec.name
                vals['contact_count'] = len(rec.org_contact_ids) if rec.org_contact_ids else 0
                if vals:
                    results.append(vals)
            return Response(json.dumps({'message': 'Data Fetch Successfully!!','total_contacts':total_contacts,'results': results}),
                            status=200,
                            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")
        except Exception as e:
            return Response(json.dumps({'message': 'Failed!!', 'reason': str(e)}), status=400,
                            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")


    @http.route('/api/org_contact/delete', auth='none', type="json", methods=['POST'])
    def org_contact_delete(self, **kwargs):
        try:
            data = request.jsonrequest
            contact_ids = data.get('contact_ids')
            deleted_ids = []
            invalid_contact_ids = []
            if not contact_ids:
                return _success_organization_error_200("Invalid Payload!!", {})
            for contact_id in contact_ids:
                res_partner_obj = request.env['res.partner'].sudo().search(
                    [('id', '=', contact_id), ('is_org_contact', '=', True)], limit=1)
                if not res_partner_obj:
                    invalid_contact_ids.append(contact_id)
                    continue
                else:
                    try:
                        res_partner_obj.unlink()
                        deleted_ids.append(res_partner_obj.id)
                    except:
                        invalid_contact_ids.append(contact_id)
                        continue
            vals = {
                'deleted': deleted_ids,
                'not_deleted': invalid_contact_ids,
            }
            return _success_200('Success', vals)
        except Exception as e:
            return _success_organization_error_200("Failed :" + str(e), {})


    def _validate_contact_data(self, data):
        REQUIRED_HEADER = ['name','email','phone','spoc_role','role_details']
        is_preferred_contact1 = True if data.get('prefer_other_detail_1') and data.get('prefer_other_detail_1').lower() == 'true' else False
        is_preferred_contact2 = True if data.get('prefer_other_detail_2') and data.get('prefer_other_detail_2').lower() == 'true' else False
        for i in REQUIRED_HEADER:
            if not data.get(i):
                return {'status': False, "result": data, "reason": "Required field: '" + i + "' data missing."}
        if data.get('phone') and not data.get('phone').isnumeric():
            return {'status': False, "result": data, "reason": "Required field: 'Phone' must be numbers and not string."}
        field_list = ['spoc_role']
        partner_obj = request.env['res.partner'].sudo()
        for i in field_list:
            if data.get(i) and data.get(i) not in list(dict(partner_obj._fields[i].selection).values()):
                return {'status': False, "result": data, "reason": "Invalid Selection value: " + i}
        for sl in field_list:
            if data.get(sl) and data.get(sl) in dict(partner_obj._fields[sl].selection).values():
                fl = dict(partner_obj._fields[sl].selection)
                data[sl] = list(fl.keys())[list(fl.values()).index(data.get(sl))]
        other_details = []
        medium_obj = request.env['utm.medium'].sudo()
        if data.get('preferred_type'):
            preferred_type = medium_obj.search([('name','=',data.get('preferred_type'))],limit=1)
            if not preferred_type:
                return {'status': False, "result": data, "reason": "'Preferred Type' Not Found."}
            else:
                data['preferred_type'] = preferred_type.id
        if data.get('other_medium_1') and data.get('other_details_1'):
            other_medium_id1 = medium_obj.search([('name','=',data.get('other_medium_1'))],limit=1)
            other_phone_code1 = data.get('other_phone_code1') if data.get('other_medium_1').lower() == 'phone' else False
            if other_medium_id1:
                other_details1 = request.env['contact.other.detail'].sudo().create(
                    {'medium_id':other_medium_id1.id, 
                    'medium_detail': data.get('other_details_1'),
                    'phone_code': other_phone_code1,
                    'enable': True if data.get('enable_other_1') and data.get('enable_other_1').lower() == 'true' else False,
                    'is_preferred_contact':is_preferred_contact1})
                other_details.append(other_details1.id)
            else:
                return {'status': False, "result": data, "reason": "'Other Medium 1' Not Found."}
        elif data.get('other_medium_1') and not data.get('other_details_1'):
            return {'status': False, "result": data, "reason": "'Other Detail 1' is required with 'Other Medium 1'."}
        if data.get('other_medium_2') and data.get('other_details_2'):
            other_medium_id2 = medium_obj.search([('name','=',data.get('other_medium_2'))],limit=1)
            other_phone_code2 = data.get('other_phone_code2') if data.get('other_medium_2').lower() == 'phone' else False
            if other_medium_id2:
                other_details2 = request.env['contact.other.detail'].sudo().create(
                    {'medium_id':other_medium_id2.id, 
                    'medium_detail': data.get('other_details_2'),
                    'phone_code': other_phone_code2,
                    'enable': True if data.get('enable_other_2') and data.get('enable_other_2').lower() == 'true' else False,
                    'is_preferred_contact':is_preferred_contact2})
                other_details.append(other_details2.id)
            else:
                return {'status': False, "result": data, "reason": "'Other Medium 2' Not Found."}
        elif data.get('preferred_type') and (is_preferred_contact1 or is_preferred_contact2):
            return {'status': False, "result": data, "reason": "Only one communication type can be set as Preferred"}
        data['other_detail_ids'] = [(6,0,other_details)]
        for i in ['other_medium_1','other_phone_code1', 'other_details_1', 'other_medium_2', 'other_phone_code2', 'other_details_2', 'prefer_other_detail_1', 'prefer_other_detail_2', 'enable_other_1', 'enable_other_2']:
            del data[i]
        data['email_enable'] = True if data.get('email_enable') and data.get('email_enable').lower() == 'true' else False
        data['phone_enable'] = True if data.get('phone_enable') and data.get('phone_enable').lower() == 'true' else False
        return {'status': True, "result": data}


    def upload_org_contact(self, header_list, data_list, org_obj):
        header = Org_Contact_Header
        success = []
        fail = []
        if all(i in header.values() for i in header_list):
            header['organisation_id'] = "Organisation"
            header['reason'] = "Reason"
            for i in range(0, len(data_list)):
                data = dict(zip(header, data_list[i]))
                data['organisation_id'] = org_obj.id
                role_details = eval(data['role_details']) if data.get('role_details') else False
                success_data = data.copy()
                fail_data = data.copy()
                res = self._validate_contact_data(data)
                del data['role_details']
                if res.get('status'):
                    try:
                        result = res.get('result')
                        result['is_org_contact'] = True
                        result['phone_code'] = result['phone_code']
                        result['property_stock_customer'] = False
                        result['property_stock_supplier'] = False
                        c_name = request.env['res.partner'].sudo().search([('organisation_id', '=', org_obj.id),'|',('email','=',result['email']),('phone','=',result['phone'])])
                        if not c_name:
                            contact_id = request.env['res.partner'].sudo().create(result)
                            success_data['contact_id'] = contact_id.id
                            self._create_spoc_details(result['spoc_role'], role_details,result['other_role'], contact_id)
                            success.append(success_data)
                        else:
                            fail_data['reason'] = "Contact Name already exists!!"
                            fail.append(fail_data)
                    except Exception as e:
                        fail_data['reason'] = "Data Not Uploaded. " + str(e)
                        fail.append(fail_data)
                else:
                    fail_data['reason'] = "Data Validation Failed in Uploaded File. " + res.get('reason')
                    fail.append(fail_data)
            return {'status': True, 'header':header, 'success': success, 'fail': fail}
        else:
            return {'status': False,'header':header, 'result':"Invalid Header in Uploaded File"}

    def _read_xls(self, cf):
        book = xlrd.open_workbook(file_contents=cf)
        sheets = book.sheet_names()
        sheet = sheets[0]
        return request.env['base_import.import']._read_xls_book(book, sheet)

    @http.route('/api/org_contact/upload', auth='none', csrf=False,  methods=['POST'])
    def org_contact_upload(self, **args):
        file = args.get('file')
        org_obj = False
        if args.get('organisation_id') and args.get('organisation_id').isdigit():
            org_id = int(args.get('organisation_id'))
            org_obj = request.env['res.partner'].sudo().search([('id','=',org_id),('is_organisation','=',True)],limit=1)
        if not org_obj:
            return Response(json.dumps("Organisation ID not found"), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")
        if file and org_obj:
            file_extension = file.filename.split('.')[-1]
            if file_extension not in ['xls','xlsx']:
                return Response(json.dumps("Only XLS or XLSX File extension allowed"), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")
            else:	
                xls_data = file.read()
                rows = self._read_xls(xls_data)[1]
                res = self.upload_org_contact(rows[0], rows[1:], org_obj)
                if res.get('status'):
                    return Response(json.dumps({'success': {'count':len(res.get('success')), 'data':res.get('success')}, \
                        "fail": {'count':len(res.get('fail')), 'header': res.get('header'), 'data':res.get('fail')}}), \
                        status = 200, \
                        headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'}, \
                        content_type = "application/json")
                else:
                    return Response(json.dumps("File Not Uploaded! " + res.get('result')), status = 400,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")
        else:
            return Response(json.dumps("Invalid request payload"), status = 200,headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,content_type = "application/json")

    def _validate_customer(self, org_ids):
        lead_obj = request.env['crm.lead'].sudo()
        customers = [org.id for org in org_ids if lead_obj.search([('partner_id', '=', org.id)])]
        return customers

    @http.route('/api/organisation_type_count', methods=["GET"], auth='none')
    def get_organisation_type_count(self):
        try:
            org_ids = request.env['res.partner'].sudo().search([('is_organisation', '=', True)])
            customers = self._validate_customer(org_ids)
            non_customers = len(org_ids)-len(customers) if len(org_ids) > len(customers) else 0
            result={
                'all_organisation': len(org_ids),
                'customers': len(customers),
                'non_customers': non_customers,
            }
            return Response(json.dumps({'message': 'success', 'resData': result, "status": True}), status=200,
                            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")
        except Exception as e:
            return Response(json.dumps({'message': 'Failed', 'resData': str(e), "status": False}), status=400,
                            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")

    def get_org_onboarding_status(self, org_id):
        return 'Onboarded' if len(org_id.bank_ids)>0 else 'Not Onboarded'

    def related_organisation_data(self, org_ids, org_type=False):
        org_list = []
        lead_ids = request.env['crm.lead'].sudo().search([('partner_id', 'in', org_ids.ids)])
        customer_ids = lead_ids.mapped('partner_id')
        if org_type and org_type.lower() == 'customer':
            org_ids = customer_ids
        elif org_type and org_type.lower() == 'non customer':
            org_ids = org_ids.filtered(lambda od: od.id not in customer_ids.ids) if customer_ids else org_ids
        for org_id in org_ids:
            onboarding = self.get_org_onboarding_status(org_id)
            org_type = self._validate_customer(org_id)
            vals = {"organisation_id": org_id.id,
                    "organisation_name": org_id.name if org_id.name else "",
                    "type": 'Customer' if org_type and org_type[0] == org_id.id  else 'Non Customer',
                    "industry": org_id.industry_id.name if org_id.industry_id else "",
                    "onboarding": onboarding,
                    "related_orgs": len(org_ids.filtered(lambda obj:obj.parent_organisation_id.id == org_id.id)),
                    "products": len(lead_ids.filtered(lambda obj:obj.partner_id.id == org_id.id).mapped('product_ids')),
                    "org_spoc": org_id.spoc_id.name if org_id.spoc_id else "",
                    "email": org_id.email if org_id.email else "",
                    "phone": org_id.phone if org_id.phone else "",
                    "is_parent_organisation": True if any(l.parent_organisation_id.id == org_id.id for l in org_ids) else False,
                    "parent_id": org_id.parent_organisation_id.id if org_id.parent_organisation_id else "",
                }
            org_list.append(vals)
        return org_list

    @http.route('/api/all_organisation_list', methods=["GET"], auth="none")
    def all_organisation_list(self, **kw):
        try:
            params = request.params
            org_obj = request.env['res.partner'].sudo()
            domain = [('is_organisation', '=', True)]
            header = ["Organisation Name", "Type", "Industry", "Onboarding", "Related Orgs",
                    "Products", "Org SPOC", "Email", "Phone"]
            limit = None
            offset = None
            if params.get('search_filter'):
                domain += [('name', 'ilike', '%'+params.get('search_filter')+'%')]
            total_org = org_obj.search_count(domain)
            if params.get('max_page') and params.get('max_page').isdigit() and params.get('min_page') and params.get(
                    'min_page').isdigit():
                limit = int(params.get('max_page')) - int(params.get('min_page'))
                offset = int(params.get('min_page'))
            org_ids = org_obj.search(domain, order='id desc', limit=limit, offset=offset)
            if params.get('organisation_type') and params.get('organisation_type').lower() not in ['customer','non customer']:
                return Response(json.dumps({'message': 'Failed', 'resData': "Invalid Organisation Type!", "status": False}),
                status=200, headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                content_type="application/json")
            org_data = self.related_organisation_data(org_ids, params.get('organisation_type'))
            return Response(json.dumps({'message': 'success', "total_record": total_org, 'header': header, 'resData': org_data, "status": True}),
                            status=200,
                            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")
        except Exception as e:
            return Response(json.dumps({'message': 'Failed', 'resData': str(e), "status": False}), status=400,
                            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")

    @http.route('/api/org/basic_information', methods=["GET"], auth="none")
    def _org_basic_information(self, **kw):
        try:
            params = request.params
            org_obj = request.env['res.partner'].sudo()
            organization = False
            if params.get('organisation_id') and params.get('organisation_id').isnumeric():
                organization = org_obj.search([('is_organisation','=',True),('id','=',params.get('organisation_id'))])
            else:
                return Response(json.dumps({'message': 'Failed', 'resData': "Organisation ID not found!", "status": False}), status = 200,
                headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,
                content_type = "application/json")
            if not organization:
                return Response(json.dumps({'message': 'Failed', 'resData': "Organisation not found!", "status": False}), status = 200,
                            headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,
                            content_type = "application/json")
            parent_org_id = organization.parent_organisation_id
            parent_org_data = {}
            related_data = []
            if parent_org_id:
                parent_org_data["id"] = parent_org_id.id
                parent_org_data["name"] = parent_org_id.name
            parent_organization = request.env['res.partner'].sudo().search(
                [('parent_organisation_id', '=', parent_org_id.id), ('is_organisation', '=', True)])
            for rec in parent_organization:
                related_data.append({"id": rec.id, "name": rec.name})
            address = ""
            if organization.street: address = address + organization.street
            if organization.street2: address = address + ", " + organization.street2
            if organization.city: address = address + ", " + organization.city
            if organization.state_id: address = address + ", " + organization.state_id.name
            if organization.country_id: address = address + ", " + organization.country_id.name
            if organization.zip: address = address + ", " + organization.zip
            organization_data = {
                "organization_id": organization.id if organization else '',
                "organization_name": organization.name if organization.name else '',
                "parent_organization": parent_org_data or "",
                "related_organization": related_data,
                "registration_number": organization.registration_no if organization.registration_no else '',
                "industry_type": organization.industry_id.name if organization.industry_id else '',
                "description": bs4.BeautifulSoup(organization.comment, features="lxml").get_text() if organization.comment else '',
                "address": address,
                "spoc_id": organization.spoc_id.id if organization.spoc_id else '',
                "spoc_name": organization.spoc_id.name if organization.spoc_id.name else '',
                "spoc_email": organization.spoc_id.email if organization.spoc_id.email else '',
                "spoc_phone_code": organization.spoc_id.phone_code if organization.spoc_id.phone_code else '',
                "spoc_phone": organization.spoc_id.phone if organization.spoc_id.phone else '',
                "preferred_type": organization.spoc_id.preferred_type if organization.spoc_id.preferred_type else ''
            }
            return Response(json.dumps({'message': 'success', 'resData': organization_data, "status": True}),
                            status=200,
                            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")
        except Exception as e:
            return Response(json.dumps({'message': 'Failed', 'resData': str(e), "status": False}), status=400,
                            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")

    def _get_billing_address(self, organisation_obj):
        billing_address = False
        if organisation_obj:
            billing_address = {
                "street": organisation_obj.invoice_address_1 if organisation_obj.invoice_address_1 else '',
                "street2": organisation_obj.invoice_address_2 if organisation_obj.invoice_address_2 else '',
                "zip": organisation_obj.invoice_zip if organisation_obj.invoice_zip else '',
                "city": organisation_obj.invoice_city if organisation_obj.invoice_city else '',
                "state": {'id': organisation_obj.invoice_state_id.id,
                        'name': organisation_obj.invoice_state_id.name if organisation_obj.invoice_state_id.name else ''},
                "country": {'id': organisation_obj.invoice_country_id.id,
                            'name': organisation_obj.invoice_country_id.name if organisation_obj.invoice_country_id.name else ''}
            }
        return billing_address

    def _get_bank_info(self, organisation_obj):
        bank_account_info = False
        if organisation_obj:
            bank_account_info = []
            for rec in organisation_obj.bank_ids:
                bank_vals = {
                    'id': rec.id,
                    'account_name': rec.acc_holder_name if rec.acc_holder_name else '',
                    'account_number': rec.acc_number if rec.acc_number else '',
                    'bank': {'id': rec.bank_id.id, 'name': rec.bank_id.name if rec.bank_id.name else ''},
                    'ifsc_code': rec.bank_id.bic if rec.bank_id.bic else '',
                    'bank_spoc_id': rec.bank_spoc_id.id,
                    'bank_spoc_name': (
                        rec.bank_spoc_id.name + " " + rec.bank_spoc_id.spoc_lname if rec.bank_spoc_id.spoc_lname else rec.bank_spoc_id.name),
                    'email': rec.bank_spoc_id.email if rec.bank_spoc_id.email else '',
                    'phone_code': rec.bank_spoc_id.phone_code if rec.bank_spoc_id.phone_code else '',
                    'phone': rec.bank_spoc_id.phone if rec.bank_spoc_id.phone else '',
                }
                bank_account_info.append(bank_vals)
        return bank_account_info

    @http.route('/api/org/billing_details', methods=["GET"], auth="none")
    def api_org_billing_details(self, **kw):
        try:
            params = request.params
            org_obj = request.env['res.partner'].sudo()
            org_id = False
            if params.get('organisation_id') and params.get('organisation_id').isnumeric():
                org_id = org_obj.search([('is_organisation','=',True),('id','=',params.get('organisation_id'))])
            else:
                return Response(json.dumps({'message': 'Failed', 'resData': "Organisation ID not found!", "status": False},
                    default=str), status=200,
                    headers={"Content-Type": "application/json","Access-Control-Allow-Origin": '*'},
                    content_type="application/json")
            if not org_id:
                return Response(json.dumps({'message': 'Failed', 'resData': "Organisation ID not found!", "status": False}), status = 200,
                            headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,
                            content_type = "application/json")
            result = {'billing_address': self._get_billing_address(org_id), 'account_details': self._get_bank_info(org_id)}
            return Response(json.dumps({'message': 'success', 'resData': result, "status": True}),
                            status=200,
                            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")
        except Exception as e:
            return Response(json.dumps({'message': 'Failed', 'resData': str(e), "status": False}, default=str),
                            status=400,
                            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")

    @http.route('/api/org/get_contact_list', methods=["GET"], auth='none')
    def api_org_get_contact_list(self, **kwargs):
        try:
            data = request.params.copy()
            contact_obj = request.env['res.partner'].sudo()
            if not data.get('organisation_id'):
                return Response(json.dumps({'message': 'Failed', 'resData': "Organisation ID not found", "status": False},
                               default=str), status=200,
                    headers={"Content-Type": "application/json",
                             "Access-Control-Allow-Origin": '*'},
                    content_type="application/json")
            requested_data = []
            org_obj = contact_obj.search([('is_organisation', '=', True), ('id', '=', data.get('organisation_id'))], limit=1)
            if not org_obj:
                return Response(json.dumps({'message': 'Failed', 'resData': "Organisation ID does not exist!","status": False},default=str), status=200,
                    headers={"Content-Type": "application/json",
                             "Access-Control-Allow-Origin": '*'},
                    content_type="application/json")
            cnt_ids = org_obj.org_contact_ids
            if data.get('search_filter'):
                cnt_ids = cnt_ids.search([('is_org_contact', '=', True),('organisation_id','=',org_obj.id),'|',('name','ilike','%'+data.get('search_filter')+'%'),('spoc_lname','ilike','%'+data.get('search_filter')+'%')])
            if cnt_ids:
                for org_contact_id in cnt_ids:
                    vals = {
                        'contact_id': org_contact_id.id,
                        'name': org_contact_id.name + " "+ org_contact_id.spoc_lname if org_contact_id.spoc_lname else org_contact_id.name,
                        'role': org_contact_id.designation if org_contact_id.designation else '',
                        'is_spoc':True,
                        'preferred_contact': org_contact_id.preferred_type if org_contact_id.preferred_type else '',
                        'preferred_contact_detail': "",
                    }
                    if org_contact_id.preferred_type and org_contact_id.preferred_type.upper() == 'PHONE':
                        phone_code = org_contact_id.phone_code + ' ' if org_contact_id.phone_code else ''
                        vals['preferred_contact_detail'] = phone_code +org_contact_id.phone if org_contact_id.phone else ''
                    elif org_contact_id.preferred_type and org_contact_id.preferred_type.upper() == 'EMAIL':
                        vals['preferred_contact_detail'] = org_contact_id.email if org_contact_id.email else ''
                    else:
                        other_preferred_id = org_contact_id.other_detail_ids.filtered(lambda obj: obj.is_preferred_contact == True)
                        if other_preferred_id:
                            vals['preferred_contact'] = other_preferred_id[0].medium_id.name
                            vals['preferred_contact_detail'] = other_preferred_id[0].medium_detail if other_preferred_id.medium_detail else ''
                    requested_data.append(vals)
            return Response(json.dumps({'message': 'success', 'resData': requested_data, "status": True}), status=200,
                            headers={"Content-Type": "application/json",
                                     "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")
        except Exception as e:
            return Response(json.dumps({'message': 'Failed', 'resData': str(e), "status": False}, default=str),
                            status=400,
                            headers={"Content-Type": "application/json",
                                     "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")


    @http.route('/api/org/product_details', methods=["GET"], auth="none")
    def _get_org_product_details(self, **kw):
        try:
            params = request.params
            org_obj = request.env['res.partner'].sudo()
            organization = False
            if params.get('organisation_id') and params.get('organisation_id').isnumeric():
                organization = org_obj.search([('is_organisation','=',True),('id','=',params.get('organisation_id'))])
            else:
                return Response(json.dumps({'message': 'fail', 'resData': "Invalid Request Payload", 'status': False}), status = 200,
                headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,
                content_type = "application/json")
            if not organization:
                return Response(json.dumps({'message': 'fail', 'resData': "Organisation Not Found", 'status': False}), status = 200,
                            headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,
                            content_type = "application/json")
            requested_data = {}
            data_list = []
            crm_lead_obj = request.env['crm.lead'].sudo().search([('partner_id', '=', organization.id)])
            for lead in crm_lead_obj:
                vals = {}
                technical_requirements = []
                vals['product_name'] = lead.product_ids.name if lead.product_ids else ''
                vals['product_varient'] = 'Best Effort'
                vals['physical_sites'] = lead.no_of_sites if lead.no_of_sites else ''
                vals['cloud_sites'] = lead.no_of_cor_sites if lead.no_of_cor_sites else ''
                if lead.security_requirement_ids:
                    for rec in lead.security_requirement_ids:
                        technical_requirement_vals = {
                            'name': rec.name if rec.name else '',
                        }
                        technical_requirements.append(technical_requirement_vals)
                vals['technical_requirements'] = technical_requirements
                vals['redundancy'] =  'No Redundancy'
                data_list.append(vals)
            requested_data['product_list'] = data_list
            return Response(json.dumps({'message': 'success', 'resData': requested_data, 'status': True}), status=200,
                            headers={"Content-Type": "application/json",
                                     "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")
        except Exception as e:
            return Response(json.dumps({'message': 'Failed', 'resData': str(e), "status": False}, default=str), status=400,
                            headers={"Content-Type": "application/json",
                                     "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")

    @http.route('/api/org/all_product_list', methods=["GET"], auth="none")
    def _get_org_all_product_list(self, **kw):
        try:
            params = request.params
            org_obj = request.env['res.partner'].sudo()
            organization = False
            if params.get('organisation_id') and params.get('organisation_id').isnumeric():
                organization = org_obj.search([('is_organisation','=',True),('id','=',params.get('organisation_id'))])
            else:
                return Response(json.dumps({'message': 'Failed', 'resData': "Organisation ID Not Found", 'status': False}), status = 200,
                headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,
                content_type = "application/json")
            if not organization:
                return Response(json.dumps({'message': 'Failed', 'resData': "Organisation Not Found", 'status': False}), status = 200,
                            headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,
                            content_type = "application/json")
            products_list = [{'id': ld.product_ids.id, 'name': ld.product_ids.name} for ld in request.env['crm.lead'].sudo().search([('partner_id', '=', organization.id),('product_ids','!=',False)])]
            return Response(json.dumps({'message': 'success', 'resData': products_list, 'status': True}),
                            status=200,
                            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")
        except Exception as e:
            return Response(json.dumps({'message': 'Failed', 'resData': str(e), "status": False}), status=400,
                            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")

    @http.route('/api/org/sales_request', methods=["GET"], auth='none')
    def api_org_sales_requests(self, **kwargs):
        try:
            params = request.params
            org_obj = request.env['res.partner'].sudo()
            organization = False
            if params.get('organisation_id') and params.get('organisation_id').isnumeric():
                organization = org_obj.search([('is_organisation','=',True),('id','=',params.get('organisation_id'))])
            else:
                return Response(json.dumps({'message': 'fail', 'resData': "Organisation ID Not Found", "status": False}), status = 200,
                headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,
                content_type = "application/json")
            if not organization:
                return Response(json.dumps({'message': 'fail', 'resData': "Organisation Not Found", "status": False}), status = 200,
                            headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,
                            content_type = "application/json")
            sales_vals = []
            lead_ids = request.env['crm.lead'].sudo().search([('partner_id', '=', organization.id)])
            for lead_obj in lead_ids:
                vals = {
                    "sales_req_id": lead_obj.id,
                    "status": "New Opportunity" if lead_obj.stage_id.name == 'New Enquiry' or lead_obj.stage_id.name == 'New' else "Service Upgrade",
                    "product": lead_obj.product_ids[0].name if len(lead_obj.product_ids)>0 else "",
                    "received": lead_obj.create_date.strftime('%d %b %Y') if lead_obj.create_date else '',
                    'updated': lead_obj.write_date.strftime('%d %b %Y') if lead_obj.write_date else '',
                    'kam': '',
                    'is_qualified': True if lead_obj.stage_id.name == 'Qualified Develop' or lead_obj.type == 'opportunity' else False
                }
                sales_vals.append(vals)
            return Response(json.dumps({'message': 'success', 'resData': sales_vals, "status": True}),
                            status=200,
                            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")
        except Exception as e:
            return Response(json.dumps({'message': 'Failed', 'resData': str(e), "status": False}), status=400,
                            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'})

    @http.route('/api/get_organisation_list', methods=["GET"], auth="none")
    def get_organisation_list(self, **kw):
        try:
            params = request.params
            org_obj = request.env['res.partner'].sudo()
            domain = [('is_organisation', '=', True)]
            header = ['Name', 'Type', 'Onboarding', 'Related Orgs', 'Products', 'YOY Revenue',
                    'CSAT Score', 'Lifetime Value', 'Pending POs', 'Open Requests']
            limit = None
            offset = None
            if params.get('search_filter'):
                domain += [('name', 'ilike','%'+params.get('search_filter')+'%')]
            total_org = org_obj.search_count(domain)
            if params.get('max_page') and params.get('max_page').isdigit() and params.get('min_page') and params.get(
                    'min_page').isdigit():
                limit = int(params.get('max_page')) - int(params.get('min_page'))
                offset = int(params.get('min_page'))
            org_ids = org_obj.search(domain, order='id desc', limit=limit, offset=offset)
            org_data = self.related_organisation_data(org_ids, params.get('organisation_type'))
            requested_data = []
            for partner in org_data:
                vals = {}
                vals['organisation_id'] = partner.get('organisation_id')
                vals['organisation_name'] = partner.get('organisation_name')
                vals['type'] = partner.get('type')
                vals['onboarding_status'] = partner.get('onboarding')
                vals['related_org'] = partner.get('related_orgs')
                vals['products'] = partner.get('products')
                vals['yoy_revenue'] = 0
                vals['csat_score'] = 0
                vals['lifetime_value'] = 0
                vals['pending_pos'] = 0
                vals['open_req'] = {'change_req':0,'cancel_req':0,'terminate_req':0,'service_req':0,'sales_req':partner.get('products')}
                requested_data.append(vals)
            return Response(json.dumps({'message': 'success', 'total_org':total_org, 'resData': requested_data, "status": True}),
                            status=200,
                            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")
        except Exception as e:
            return Response(json.dumps({'message': 'Failed', 'resData': str(e), "status": False}), status=400,
                            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")
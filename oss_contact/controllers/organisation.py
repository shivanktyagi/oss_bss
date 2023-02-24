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

    @http.route('/api/organisation/accounts/dropdown', methods=["GET"], auth="none")
    def organisation_accounts_dropdown(self, **kwargs):
        try:
            params = request.params
            org_id = False
            if params.get('organisation_id') and params.get('organisation_id').isdigit():
                org_id = int(params.get('organisation_id'))
            org = request.env['res.partner'].sudo().browse(org_id).exists()
            account_ids = org.bank_ids if org else request.env['res.partner.bank'].sudo().search([])
            accounts = [{'id': account.id, 'name': account.acc_holder_name if account.acc_holder_name else ''} for account in account_ids if account.acc_holder_name]
            return Response(json.dumps(accounts), status=200,
                            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")
        except Exception as e:
            return Response(json.dumps({'message': 'Failed!!', 'reason': str(e)}), status=400,
                            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")

    @http.route('/api/organisation/sites/dropdown', methods=["GET"], auth="none")
    def organisation_sites_dropdown(self, **kwargs):
        try:
            params = request.params
            org_id = False
            if params.get('organisation_id') and params.get('organisation_id').isdigit():
                org_id = int(params.get('organisation_id'))
            org = request.env['res.partner'].sudo().browse(org_id).exists()
            org_id = org_id if org_id else False
            site_ids = request.env['res.partner'].sudo().search([('is_site','=',True),('organisation_id','=',org_id)])
            sites = [{'id': site.id, 'name': site.name_of_site if site.name_of_site else ''} for site in site_ids if site.name_of_site]
            return Response(json.dumps(sites), status=200,
                            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")
        except Exception as e:
            return Response(json.dumps({'message': 'Failed!!', 'reason': str(e)}), status=400,
                            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")

    @http.route('/api/get_all_contact_list', methods=["GET"], auth="none")
    def get_all_contact_list(self, **kw):
        try:
            params = request.params
            contact_obj = request.env['res.partner'].sudo()
            domain = [('is_org_contact','=',True)]
            if params.get('search_filter'):
                domain += [('name','ilike',params.get('search_filter'))]
            limit = None
            offset = None
            if params.get('organisation_id') and params.get('organisation_id').isdigit():
                domain += [('organisation_id','=',int(params.get('organisation_id')))]
            contact_count = contact_obj.search_count(domain)
            if params.get('max_page') and params.get('max_page').isdigit() and params.get('min_page') and params.get('min_page').isdigit():
                limit = int(params.get('max_page')) - int(params.get('min_page'))
                offset = int(params.get('min_page'))
            # if params.get('contact_id') and params.get('organisation_id').isdigit():
            #     domain += [('id','=',int(params.get('contact_id')))]
            contact_ids = contact_obj.search(domain, order='id desc', limit=limit, offset=offset)
            contact_list = []
            if not contact_ids:
                return Response(json.dumps({"total_record": contact_count, 'data': contact_list}), status = 200,
                            headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,
                            content_type = "application/json")
            header = ["Organisation", "Employee ID", "Name", "Role", "Preferred Contact Medium", "Preferred Contact Details", "Email", "Phone"]
            for contact_id in contact_ids:
                last_name = " " +contact_id.spoc_lname if contact_id.spoc_lname else ""
                preferred_contact_medium = False
                preferred_contact_details = False
                if contact_id.preferred_type and contact_id.preferred_type.lower() == 'email':
                    preferred_contact_medium = 'Email'
                    preferred_contact_details = contact_id.email
                elif contact_id.preferred_type and contact_id.preferred_type.lower() == 'phone':
                    preferred_contact_medium = 'Phone'
                    preferred_contact_details = contact_id.phone
                else:
                    other_id = contact_id.other_detail_ids.filtered(lambda od: od.is_preferred_contact == True)
                    preferred_contact_medium = other_id[0].medium_name if len(other_id)>0 else False
                    preferred_contact_details = other_id[0].medium_detail if len(other_id)>0 else False
                vals = {
                    "contact_id": contact_id.id,
                    "organisation_name": contact_id.organisation_id.name if contact_id.organisation_id and contact_id.organisation_id.name else "",
                    "organisation_id": contact_id.organisation_id.id if contact_id.organisation_id else "",
                    "emp_id": contact_id.emp_id if contact_id.emp_id else "",
                    "name": contact_id.name + last_name if contact_id.name or last_name else "",
                    "role": contact_id.designation if contact_id.designation else "",
                    "preferred_contact_medium": preferred_contact_medium if preferred_contact_medium else "",
                    "preferred_contact_details": preferred_contact_details if preferred_contact_details else "",
                    "email": contact_id.email if contact_id.email else "",
                    "phone_code": contact_id.phone_code if contact_id.phone_code else "",
                    "phone": contact_id.phone if contact_id.phone else "",
                }
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
            contact_list = []
            if not contact_id:
                return Response(json.dumps({"message":"Contact Not Found"}), status = 200,
                            headers = {"Content-Type":"application/json","Access-Control-Allow-Origin":'*'} ,
                            content_type = "application/json")
            other_details = False
            if contact_id.other_detail_ids:
                other_details = [{"id": cd.medium_id.id,"name":cd.medium_name,"details": cd.medium_detail,"is_preferred":'Yes' if cd.is_preferred_contact else 'No'} for cd in contact_id.other_detail_ids]
            remarks = False
            if contact_id.comment:
                remarks = bs4.BeautifulSoup(contact_id.comment,features="lxml")
            account_ids = request.env['res.partner.bank'].sudo().search([('bank_spoc_id','=',contact_id.id)])
            accounts = [{'id': account.id, 'name': account.acc_holder_name if account.acc_holder_name else ''} for account in account_ids if account.acc_holder_name]
            site_ids = request.env['res.partner'].sudo().search([('email','=',contact_id.email),('mobile','=',contact_id.phone)])
            sites = [{'id': site.id, 'name': site.name_of_site if site.name_of_site else ''} for site in site_ids if site.name_of_site]
            vals = {
                "contact_id": contact_id.id,
                "first_name": contact_id.name if contact_id.name else "",
                "last_name": contact_id.spoc_lname if contact_id.spoc_lname else "",
                "role": contact_id.designation if contact_id.designation else "",
                "organisation_name": contact_id.organisation_id.name if contact_id.organisation_id and contact_id.organisation_id.name else "",
                "organisation_id": contact_id.organisation_id.id if contact_id.organisation_id else "",
                "emp_id": contact_id.emp_id if contact_id.emp_id else "",
                "email": contact_id.email if contact_id.email else "",
                "phone_code": contact_id.phone_code if contact_id.phone_code else "",
                "phone": contact_id.phone if contact_id.phone else "",
                "other_details": other_details if other_details else "",
                "preferred_type": contact_id.preferred_type if contact_id.preferred_type else "",
                "remarks": remarks.get_text() if remarks else "",
                "accounts": accounts,
                "sites": sites,
                "image": base64.b64encode(contact_id.image_1920).decode('utf-8') if contact_id.image_1920 else ''
            }
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
            data.get('spoc_first_name') and data.get('spoc_email') and \
            data.get('phone_code') and data.get('spoc_phone')):
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
                    # "phone_code": data.get("spoc_phone_code"),
                    "phone": data.get("spoc_phone"),
                    "is_org_contact": True
                }
                org_spoc_id = res_partner_obj.create(spoc_vals)
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
                if request.env['res.partner.bank'].sudo().search([('sanitized_acc_number','=',rec.get('account_number'))]):
                    return _success_organization_error_200("Account Number Already Exist! :",{})
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
                    # "name": rec.get('bank_first_name') +  rec.get('bank_last_name') if rec.get('bank_last_name') else rec.get('bank_first_name'),
                    "email": rec.get('bank_email'),
                    # "bank_phone_code": rec.get('phone_code'),
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
            header = ["First Name", "Last Name", "Role", "Employee ID", "Preferred Type", "Email", "Phone",
            "Other Medium 1", "Other Details 1", "Prefer Other Detail 1", "Other Medium 2",
            "Other Details 2", "Prefer Other Detail 2", "Org SPOC", "Bank SPOC", "Accounts", "Site SPOC",
            "Sites","Remarks"]
            return Response(json.dumps({'success': True, 'status': 'Success', 'header': header}), status=200,
                headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                content_type="application/json")
        except Exception as e:
            return Response(json.dumps({'success': False, 'status': 'Failed Due To: ' + str(e)}), status=200,
                            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")

    @http.route('/api/org_contact/update', type="json", methods=["POST"], auth="none")
    def update_contact(self, **kw):
        data = request.jsonrequest
        contact_id = data.get('contact_id')
        try:
            contact = request.env['res.partner'].sudo().search([('id', '=', contact_id), ('is_org_contact', '=', True)],
                                                               limit=1)
            if not contact:
                return _success_organization_error_200("Contact Id Not Found", {})
            value = []
            other_detail_ids = request.env['contact.other.detail'].sudo()
            if data.get('organisation_id') != contact.organisation_id.id:
                return _success_organization_error_200("Organisation ID cannot be Updated. ", {})
            if data.get('other_details'):
                for rec in data.get('other_details'):
                    medium_id = request.env['utm.medium'].sudo().browse(rec.get('medium_id')).exists()
                    if not medium_id:
                        return _success_organization_error_200("Contact Other Details Id Not Exist ", {})
                    old_other_id = other_detail_ids.search(
                        ['|', ('medium_id', '=', medium_id.id), ('medium_detail', '=', rec.get('medium_detail'))])
                    if not old_other_id:
                        other_id = other_detail_ids.create(
                            {"medium_id": medium_id.id, "medium_detail": rec.get('medium_detail'), "is_preferred_contact": rec.get("is_preferred_contact")})
                        value.append(other_id.id)
                    else:
                        old_other_id.medium_id = medium_id.id
                        old_other_id.medium_detail = rec.get('medium_detail')
                        old_other_id.is_preferred_contact = rec.get("is_preferred_contact")
            if data.get('is_org_spoc').upper() == 'YES':
                org_contact_obj = request.env['res.partner'].sudo().search(
                    [('is_org_contact', '=', True), ('organisation_id', '=', int(data.get('organisation_id')))])
                for org_contact in org_contact_obj:
                    if org_contact.is_org_spoc:
                        return _success_organization_error_200("Another Contact exist as Org SPOC for this organisation. Remove them as SPOC to set this contact as the New SPOC.",{})
            if data.get('preferred_type') and (data.get('other_details')):
                for rec in data.get('other_details'):
                    if rec.get('is_preferred_contact').upper() == 'YES':
                        return _success_organization_error_200("Only one communication type can be set as Preferred", {})
            if data.get('is_bank_spoc').upper() == 'YES':
                for rec in data.get('accounts'):
                    account_id = request.env['res.partner.bank'].sudo().browse(rec).exists()
                    if account_id:
                        account_id.bank_spoc_id = contact.id
            if data.get('is_site_spoc').upper() == 'YES':
                for rec in data.get('sites'):
                    site_id = request.env['res.partner'].sudo().search([('id', '=', rec), ('is_site', '=', True)]).exists()
                    if site_id:
                        vals = {
                            'name': contact.name,
                            'spoc_lname': contact.spoc_lname,
                            'email': contact.email,
                            'phone_code': contact.phone_code,
                            'phone': contact.phone
                        }
                        site_id.write(vals)
            try:
                vals = {
                    'name': data.get('first_name') if data.get('first_name') else contact.name,
                    'spoc_lname': data.get('last_name') if data.get('last_name') else contact.spoc_lname,
                    'organisation_id': data.get('organisation_id') if data.get(
                        'organisation_id') else contact.organisation_id,
                    'designation': data.get('role') if data.get('role') else contact.designation,
                    'emp_id': data.get('emp_id') if data.get('emp_id') else contact.emp_id,
                    'phone_code': data.get('phone_code') if data.get('phone_code') else contact.phone_code,
                    'phone': data.get('phone') if data.get('phone') else contact.phone,
                    'email': data.get('email') if data.get('email') else contact.email,
                    "preferred_type": data.get('preferred_type') if data.get('preferred_type') else contact.preferred_type,
                    'is_org_spoc': True if data.get('is_org_spoc').upper() == 'YES' else False,
                    'is_bank_spoc': True if data.get('is_bank_spoc').upper() == 'YES' else False,
                    'is_site_spoc': True if data.get('is_site_spoc').upper() == 'YES' else False,
                    'other_detail_ids': [(4, v) for v in value] if value else contact.other_detail_ids.ids,
                    'comment': data.get('remarks') if data.get('remarks') else contact.comment
                }
                contact.sudo().write(vals)
                return _success_organization_200('Contact Details Successfully Updated.', {})
            except Exception as e:
                return _success_organization_error_200("Contact Details Not Updated." + str(e), {})
        except Exception as e:
            return _success_organization_error_200("Invalid request payload. " + str(e), {})

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
            if data.get('is_org_spoc').upper() == 'YES':
                org_contact_obj = request.env['res.partner'].sudo().search(
                    [('is_org_contact', '=', True), ('organisation_id', '=', org_obj.id)])
                for org_contact in org_contact_obj:
                    if org_contact.is_org_spoc:
                        return _success_organization_error_200("Another Contact exist as Org SPOC for this organisation. Remove them as SPOC to set this contact as the New SPOC.", {})
            if data.get('preferred_type') and (data.get('other_details')):
                for rec in data.get('other_details'):
                    if rec.get('is_preferred_contact').upper() == 'YES':
                        return _success_organization_error_200("Only one communication type can be set as Preferred",{})
            vals = {
                'name': data.get('first_name'),
                'spoc_lname': data.get('last_name') if data.get('last_name') else False,
                'organisation_id': org_obj.id,
                'emp_id': data.get('emp_id'),
                'designation': data.get('role'),
                'email': data.get('email'),
                'phone_code': data.get('phone_code') if data.get('phone_code') else False,
                'phone': data.get('phone'),
                'preferred_type': data.get('preferred_type') if data.get('preferred_type') else False,
                'is_org_spoc': True if data.get('is_org_spoc').lower() == 'yes' else False,
                'is_bank_spoc': True if data.get('is_bank_spoc').lower() == 'yes' else False,
                'is_site_spoc': True if data.get('is_site_spoc').lower() == 'yes' else False,
                'comment': data.get('remark') if data.get('remark') else False,
                'property_stock_customer': False,
                'property_stock_supplier': False,
                'is_org_contact': True
            }
            res_partner_obj = request.env['res.partner'].sudo().create(vals)
            if data.get('is_bank_spoc').lower() == 'yes':
                if data.get('accounts'):
                    for bank_acc in data.get('accounts'):
                        accounts = request.env['res.partner.bank'].sudo().browse(bank_acc).exists()
                        if accounts:
                            accounts.sudo().write({'bank_spoc_id': res_partner_obj.id})
            if data.get('is_site_spoc').lower() == 'yes':
                if data.get('sites'):
                    for site_id in data.get('sites'):
                        sites = request.env['res.partner'].sudo().search([('id', '=', site_id), ('is_site', '=', True)],limit=1)
                        if sites:
                            sites.sudo().write(
                                {'name': data.get('first_name'),
                                 'spoc_lname': data.get('last_name') if data.get('last_name') else '',
                                 'email': data.get('email'),
                                 'mobile': data.get('phone')
                                 })
            if data.get('other_details'):
                for rec in data.get('other_details'):
                    if rec.get('is_preferred_contact').upper() == 'YES':
                        rec['is_preferred_contact'] = True
                    else:
                        rec['is_preferred_contact'] = False
                    create_other_details = request.env['contact.other.detail'].sudo().create(rec)
                    other_medium_ids.append(create_other_details.id)
            res_partner_obj.other_detail_ids = [(6, 0, other_medium_ids)]
            return _success_organization_200("Contact Created Successfully !!", {'id': res_partner_obj.id})
        except Exception as e:
            return _success_organization_error_200("Failed :" + str(e), {})

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
        REQUIRED_HEADER = ['name','designation','email','phone']
        is_preferred_contact1 = True if data.get('prefer_other_detail_1') and data.get('prefer_other_detail_1').lower() == 'yes' else False
        is_preferred_contact2 = True if data.get('prefer_other_detail_2') and data.get('prefer_other_detail_2').lower() == 'yes' else False
        for i in REQUIRED_HEADER:
            if not data.get(i):
                return {'status': False, "result": data, "reason": "Required field: '" + i + "' data missing."}
        if data.get('phone') and not data.get('phone').isnumeric():
            return {'status': False, "result": data, "reason": "Required field: '" + i + "' must be numbers and not string."}
        other_details = []
        medium_obj = request.env['utm.medium'].sudo()
        if data.get('preferred_contact_medium') and data.get('preferred_contact_details'):
            preferred_contact_medium = medium_obj.search([('name','=',data.get('preferred_contact_medium'))],limit=1)
            if not preferred_contact_medium:
                return {'status': False, "result": data, "reason": "'Preferred Contact Medium' Not Found."}
            else:
                data['preferred_contact_medium'] = preferred_contact_medium.id
        elif data.get('preferred_contact_medium') and not data.get('preferred_contact_details'):
            return {'status': False, "result": data, "reason": "'Preferred Contact Detail' is required with 'Preferred Contact Medium'."}
        if data.get('other_medium_1') and data.get('other_details_1'):
            other_medium_id1 = medium_obj.search([('name','=',data.get('other_medium_1'))],limit=1)
            if other_medium_id1:
                other_details1 = request.env['contact.other.detail'].sudo().create({'medium_id':other_medium_id1.id, 'medium_detail': data.get('other_details_1'),'is_preferred_contact':is_preferred_contact1})
                other_details.append(other_details1.id)
            else:
                return {'status': False, "result": data, "reason": "'Other Medium 1' Not Found."}
        elif data.get('other_medium_1') and not data.get('other_details_1'):
            return {'status': False, "result": data, "reason": "'Other Detail 1' is required with 'Other Medium 1'."}
        if data.get('other_medium_2') and data.get('other_details_2'):
            other_medium_id2 = medium_obj.search([('name','=',data.get('other_medium_2'))],limit=1)
            if other_medium_id2:
                other_details2 = request.env['contact.other.detail'].sudo().create({'medium_id':other_medium_id2.id, 'medium_detail': data.get('other_details_2'),'is_preferred_contact':is_preferred_contact2})
                other_details.append(other_details2.id)
            else:
                return {'status': False, "result": data, "reason": "'Other Medium 2' Not Found."}
        elif data.get('preferred_type') and (is_preferred_contact1 or is_preferred_contact2):
            return {'status': False, "result": data, "reason": "Only one communication type can be set as Preferred"}
        data['other_detail_ids'] = [(6,0,other_details)]
        del data['other_medium_1']
        del data['other_details_1']
        del data['other_medium_2']
        del data['other_details_2']
        del data['prefer_other_detail_1']
        del data['prefer_other_detail_2']
        data['is_org_spoc'] = True if data.get('is_org_spoc') and data.get('is_org_spoc').lower() == 'yes' else False
        data['is_bank_spoc'] = True if data.get('is_bank_spoc') and data.get('is_bank_spoc').lower == 'yes' else False
        data['is_site_spoc'] = True if data.get('is_site_spoc') and data.get('is_site_spoc').lower() == 'yes' else False
        return {'status': True, "result": data}


    def upload_org_contact(self, header_list, data_list, org_obj):
        header = {"name":"First Name",
                "spoc_lname": "Last Name",
                "designation": "Role",
                "emp_id": "Employee ID",
                "preferred_type": "Preferred Type",
                "email": "Email",
                "phone": "Phone",
                "other_medium_1": "Other Medium 1",
                "other_details_1": "Other Details 1",
                "prefer_other_detail_1": "Prefer Other Detail 1",
                "other_medium_2": "Other Medium 2",
                "other_details_2": "Other Details 2",
                "prefer_other_detail_2": "Prefer Other Detail 2",
                "is_org_spoc": "Org SPOC",
                "is_bank_spoc": "Bank SPOC",
                "accounts": "Accounts",
                "is_site_spoc": "Site SPOC",
                "sites": "Sites",
                "comment": "Remarks",
                }
        success = []
        fail = []
        if all(i in header.values() for i in header_list):
            header['organisation_id'] = "Organisation"
            header['reason'] = "Reason"
            for i in range(0, len(data_list)):
                data = dict(zip(header, data_list[i]))
                data['organisation_id'] = org_obj.id
                site_ids = eval(data['sites']) if data.get('sites') else False
                bank_ids = eval(data['accounts']) if data.get('accounts') else False
                success_data = data.copy()
                fail_data = data.copy()
                res = self._validate_contact_data(data)
                del data['accounts']
                del data['sites']
                if res.get('status'):
                    try:
                        result = res.get('result')
                        result['is_org_contact'] = True
                        result['property_stock_customer'] = False
                        result['property_stock_supplier'] = False
                        c_name = request.env['res.partner'].sudo().search([('organisation_id', '=', org_obj.id),'|',('email','=',result['email']),('phone','=',result['phone'])])
                        if not c_name:
                            contact_id = request.env['res.partner'].sudo().create(result)
                            success_data['contact_id'] = contact_id.id
                            if bank_ids:
                                accounts = request.env['res.partner.bank'].sudo().browse(bank_ids)
                                accounts.sudo().write({'bank_spoc_id':contact_id.id})
                            if site_ids:
                                sites = request.env['res.partner'].sudo().search([('is_site','=',True),('id','in',site_ids)])
                                sites.sudo().write({'name':contact_id.name,'spoc_lname':contact_id.spoc_lname,'email':contact_id.email,'mobile':contact_id.phone})
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
        lead_ids = request.env['crm.lead'].sudo().search([('partner_id', 'in', org_ids.ids)])
        customers = len(lead_ids.filtered(lambda obj: obj.type == 'opportunity'))
        return {'customers': customers, 'non_customers': len(org_ids)-customers}

    @http.route('/api/organisation_type_count', methods=["GET"], auth='none')
    def get_organisation_type_count(self):
        try:
            org_ids = request.env['res.partner'].sudo().search([('is_organisation', '=', True)])
            res = self._validate_customer(org_ids)
            result={
                'all_organisation': len(org_ids),
                'customers': res.get('customers'),
                'non_customers': res.get('non_customers'),
            }
            return Response(json.dumps(result), status=200,
                            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")
        except Exception as e:
            return Response(json.dumps({'message': 'Failed!!', 'reason': str(e)}), status=400,
                            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": '*'},
                            content_type="application/json")
import csv
import io
import xlrd
from odoo import models, fields, api, _
import base64
import logging
_logger = logging.getLogger(__name__)

PREDEFINED_HEADER = {'name_of_site': "Name Of Site",
                    'site_type': 'Type Of Site',
                    'hosting_models': 'Hosting Model',
                    'street': "Site Address Line 1",
                    'street2': "Site Address Line 2",
                    'zip': 'Pin Code/Zip Code',
                    'city': 'City',
                    'state_id': 'State',
                    'country_id': 'Country',
                    'partner_latitude': 'Latitude',
                    'partner_longitude': 'Longitude',
                    "name": "SPOC First Name",
                    "spoc_lname": "SPOC Last Name",
                    "mobile": "Contact  Number",
                    "email": "Email",
                    "last_mile_connectivity": "Do you Have SITA Last Mile Connectivity",
                    "existing_id": "Existing Id For Transport Link",
                    "existing_site_code": "Existing site Code",
                    "redundancy_requirement": "Redundency Requirement",
                    "tp_1_type": "Transport Link 1 Type",
                    "tp_1_media": "Transport Link 1 Media",
                    "tp_1_sla": "Transport Link 1 SLA",
                    "tp_1_bandwidth": "Transport Link 1 Bandwidth value",
                    "tp_1_bandwidth_type": "Transport Link 1 Bandwidth unit",
                    "tp_2_type": "Transport Link 2 Type",
                    "tp_2_media": "Transport Link 2 Media",
                    "tp_2_sla": "Transport Link 2 SLA",
                    "tp_2_bandwidth": "Transport Link 2 Bandwidth value",
                    "tp_2_bandwidth_type": "Transport Link 2 Bandwidth unit",
                    "hardware_router1": "Hardware Router 1",
                    "hardware_router2": "Hardware Router 2",
                    "hardware_support_level": "Hardware Support Level",
                    "site_sla": "Site SLA",
                    "wireless_for_lan": "Wireless For LAN",
                    "site_internet_usage": "Internet Usage",
                }


REQUIRED_HEADER = ['name_of_site','site_type','hosting_models', 'street', 'street2', 'zip', 'city', 'state_id', 'country_id', 'partner_latitude', 'partner_longitude',   'name','spoc_lname', 'mobile', 'email', 'redundancy_requirement', 'tp_1_type', 'tp_1_bandwidth', 'tp_1_bandwidth_type', 'tp_1_sla', 'tp_1_media', 'hardware_router1']

class CrmLead(models.Model):
    _inherit = 'crm.lead'
    _description = 'CRM Leads'

    import_sites_csv = fields.Binary(string='Import sites', attachment=False, tracking=True)
    file_name = fields.Char("File Name")

    def _validate_csv_data(self, data):
        partner_obj = self.env['res.partner'].sudo()
        field_list = ['site_type','hosting_models','last_mile_connectivity','redundancy_requirement','wireless_for_lan','site_internet_usage']
        for i in field_list:
            if data.get(i) and data.get(i) not in list(dict(partner_obj._fields[i].selection).values()):
                return {'status': False, "result": data, "reason": "Invalid Selection value: " + i}
        for sl in field_list:
            if data.get(sl) and data.get(sl) in dict(self.env['res.partner'].sudo()._fields[sl].selection).values():
                fl = dict(partner_obj._fields[sl].selection)
                data[sl] = list(fl.keys())[list(fl.values()).index(data.get(sl))]
        for i in REQUIRED_HEADER:
            if not data.get(i):
                return {'status': False, "result": data, "reason": "Required field: '" + i + "' data missing."}
        for i in data:
            if data.get(i) == '':
                data[i] = False
        for i in ['tp_1_type', 'tp_2_type']:
            if data.get(i) and data.get(i) not in list(dict(self.env['transport.links'].sudo()._fields['tp_type'].selection).values()):
                return {'status': False, "result": data, "reason": "Invalid Selection value: " + i}
            elif data.get(i):
                fl = dict(self.env['transport.links'].sudo()._fields['tp_type'].selection)
                data[i] = list(fl.keys())[list(fl.values()).index(data.get(i))]
        for i in ['tp_1_media', 'tp_2_media']:
            if data.get(i) and data.get(i) not in list(dict(self.env['transport.links'].sudo()._fields['tp_media'].selection).values()):
                return {'status': False, "result": data, "reason": "Invalid Selection value: " + i}
            elif data.get(i):
                fl = dict(self.env['transport.links'].sudo()._fields['tp_media'].selection)
                data[i] = list(fl.keys())[list(fl.values()).index(data.get(i))]
        for i in ['tp_1_bandwidth_type', 'tp_2_bandwidth_type']:
            if data.get(i) and data.get(i) not in list(dict(self.env['transport.links'].sudo()._fields['bandwidth_type'].selection).values()):
                return {'status': False, "result": data, "reason": "Invalid Selection value: " + i}
            elif data.get(i):
                fl = dict(self.env['transport.links'].sudo()._fields['bandwidth_type'].selection)
                data[i] = list(fl.keys())[list(fl.values()).index(data.get(i))]
        if data.get('partner_latitude'):
            data['partner_latitude'] = float(data.get('partner_latitude'))
        if data.get('partner_longitude'):
            data['partner_longitude'] = float(data.get('partner_longitude'))
        if data.get('mobile'):
            data['mobile'] = int(data.get('mobile'))
        if data.get('last_mile_connectivity') and data.get('last_mile_connectivity') == 'yes' and not (data.get("existing_id") or data.get("existing_site_code")):
            return {'status': False, "result": data, "reason": "'existing_id' or 'existing_site_code' missing in case of 'last_mile_connectivity' as 'yes'"}
        if data.get('country_id') and not self.env['res.country'].sudo().search([('name', '=like', data.get('country_id'))], limit=1):
            return {'status': False, "result": data, "reason": "Country Not Found."}
        else:
            data['country_id'] = self.env['res.country'].sudo().search([('name', '=like', data.get('country_id'))], limit=1).id
        if data.get('state_id') and not self.env['res.country.state'].sudo().search([('name', '=like', data.get('state_id'))], limit=1):
            return {'status': False, "result": data, "reason": "State Not Found."}
        else:
            data['state_id'] = self.env['res.country.state'].sudo().search([('name', '=like', data.get('state_id'))], limit=1).id
        return {'status': True, "result": data}

    def upload_csv_file(self, header_list, csv_data):
        warning_msg = [("Row", "Status", "Response")]
        tp_data = ['tp_1_type','tp_1_bandwidth', 'tp_1_bandwidth_type', 'tp_1_sla','tp_1_media','tp_2_type','tp_2_bandwidth', 'tp_2_bandwidth_type', 'tp_2_sla','tp_2_media']
        success = []
        fail = []
        cnt = 1
        if all(i in PREDEFINED_HEADER.values() for i in header_list):
            for i in range(0, len(csv_data)):
                data_list = dict(zip(PREDEFINED_HEADER, csv_data[i]))
                success_data = data_list.copy()
                fail_data = data_list.copy()
                res = self._validate_csv_data(data_list)
                tp_data1 = {}
                tp_data1['tp_type'] = fail_data.get('tp_1_type')
                tp_data1['tp_bandwidth'] = fail_data.get('tp_1_bandwidth')
                tp_data1['tp_bandwidth'] = fail_data.get('tp_1_bandwidth')
                tp_data1['bandwidth_type'] = fail_data.get('tp_1_bandwidth_type')
                tp_data1['tp_media'] = fail_data.get('tp_1_media')
                tp_data2 = {}
                tp_data2['tp_type'] = fail_data.get('tp_2_type')
                tp_data2['tp_bandwidth'] = fail_data.get('tp_2_bandwidth')
                tp_data2['tp_bandwidth'] = fail_data.get('tp_2_bandwidth_type')
                tp_data2['tp_sla'] = fail_data.get('tp_2_sla')
                tp_data2['tp_media'] = fail_data.get('tp_2_media')
                for td in tp_data:
                    del fail_data[td]
                fail_data['tp_link1'] = tp_data1
                fail_data['tp_link2'] = tp_data2
                fields_update = ['site_type','hosting_models','state_id', 'country_id']
                for fu in fields_update:
                    success_data[fu] = res.get('result')[fu] if res.get('result')[fu] else ''
                    fail_data[fu] = res.get('result')[fu] if res.get('result')[fu] else ''
                if res.get('status'):
                    try:
                        result = res.get('result')
                        rt1 = []
                        if result.get('hardware_router1'):
                            rt_id1 = self.env['product.product'].sudo().search([('name','=like',result.get('hardware_router1'))]).id
                            if rt_id1:
                                rt1.append(rt_id1)
                        if result.get('hardware_router2'):
                            rt_id2 = self.env['product.product'].sudo().search([('name','=like',result.get('hardware_router2'))]).id
                            if rt_id2:
                                rt1.append(rt_id2)
                        result['router_ids'] = [(6,0,rt1)] if rt1 else False
                        del result['hardware_router1']
                        del result['hardware_router2']
                        result['is_site'] = True
                        result['is_company'] = True
                        result['partner_site_id'] = self.id
                        tp_data1 = {}
                        tp_data1['tp_type'] = result.get('tp_1_type') or ''
                        tp_data1['tp_bandwidth'] = result.get('tp_1_bandwidth') or ''
                        tp_data1['tp_bandwidth'] = result.get('tp_1_bandwidth_type') or ''
                        tp_data1['tp_sla'] = result.get('tp_1_sla') or ''
                        tp_data1['tp_media'] = result.get('tp_1_media') or ''
                        tp_data2 = {}
                        tp_data2['tp_type'] = result.get('tp_2_type') or ''
                        tp_data2['tp_bandwidth'] = result.get('tp_2_bandwidth') or ''
                        tp_data2['tp_bandwidth'] = result.get('tp_2_bandwidth_type') or ''
                        tp_data2['tp_sla'] = result.get('tp_2_sla') or ''
                        tp_data2['tp_media'] = result.get('tp_2_media') or ''
                        for td in tp_data:
                            del result[td]
                            del success_data[td]
                        success_data['tp_link1'] = tp_data1
                        success_data['tp_link2'] = tp_data2
                        tp_id1 = self.env['transport.links'].sudo().create(tp_data1)
                        tp_id2 = self.env['transport.links'].sudo().create(tp_data2)
                        result['tp_link_model_id'] = [(6,0,[tp_id1.id,tp_id2.id])]
                        result['property_stock_customer'] = False
                        result['property_stock_supplier'] = False
                        c_name = self.env['res.partner'].sudo().search([('name_of_site', '=ilike', result['name_of_site']),('partner_site_id', '=', self.id)])
                        if not c_name:
                            site_id = self.env['res.partner'].sudo().create(result)
                            warning_msg += [(str(i+1), "Success", "Data Uploaded Successfully.")]
                            success_data['site_id'] = site_id.id
                            success.append(success_data)
                        else:
                            warning_msg += [(str(i+1), "Fail", "Site Name already exists, please add unique name." )]
                            fail.append({str(cnt): fail_data, 'reason': "Site Name already exists, please add unique name." })
                            cnt += 1
                    except Exception as e:
                        warning_msg += [(str(i+1), "Fail", "Data Not Uploaded. " + str(e))]
                        fail.append({str(cnt): fail_data, 'reason': "Data Not Uploaded. " + str(e)})
                        cnt += 1
                else:
                    warning_msg += [(str(i+1), "Fail", "Data Validation Failed in CSV File" + res.get('reason'))]
                    fail.append({str(cnt): fail_data, 'reason': "Data Validation Failed in CSV File. " + res.get('reason')})
                    cnt += 1
            if self.import_sites_csv:
                self.env['ir.attachment'].sudo().create({
                    'name': self.file_name ,
                    'datas': self.import_sites_csv,
                    'type': 'binary',
                    'res_model': 'crm.lead',
                    'res_id': self.id,
                })
            self.import_sites_csv = self.file_name = False
            return {'status': True, 'result':warning_msg, 'success': success, 'fail': fail}
        else:
            return {'status': False, 'result':"Invalid Header in CSV File"}

    def _read_xls(self, cf):
        book = xlrd.open_workbook(file_contents=cf)
        sheets = book.sheet_names()
        sheet = sheets[0]
        return self.env['base_import.import']._read_xls_book(book, sheet)

    def import_csv(self):
        if self.import_sites_csv:
            csv_data = base64.decodebytes(self.import_sites_csv)
            rows = self._read_xls(csv_data)[1]
            res_csv = self.upload_csv_file(rows[0], rows[1:])
            if res_csv.get('status'):
                warning_msg = res_csv.get('result')
                msg = "<table border=1 style='width:100%;'>"
                msg += "<thead>"
                for i in warning_msg[0]:
                    msg += "<th class='p-4'>" + i +"</th>"
                msg += "</thead>"
                for i in warning_msg[1:]:
                    msg += "<tr>"
                    for j in i:
                        msg += "<td class='p-4'>" + j +"</td>"
                    msg += "</tr>"
                msg += "</table>"
                return self.env['message.wizard'].show_message(msg)
            else:
                return self.env['message.wizard'].show_message(res_csv.get('result'))
        else:
            return False

class Messagewizard(models.TransientModel):
    _name = "message.wizard"
    _description = "Message wizard"

    message = fields.Char()

    def show_message(self, message, name='Message/Summary'):
        view_id = self.env.ref('oss_contact.message_wizard_form').id
        wizard_id = self.create({'message': message})
        return {
            'name': name,
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'message.wizard',
            'res_id': wizard_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }

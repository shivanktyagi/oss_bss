# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2022 (https://www.in2ittech.com)
#
##############################################################################
import logging


from odoo import models, api, fields, exceptions
from lxml import etree
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class ExtraConfig(models.Model):
    _name = 'form.extra.config'
    _description = 'Form extra config'

    name = fields.Char(required=True)

class ExtraConfigLines(models.Model):
    _name = 'form.extra.config.lines'
    _description = 'Form extra config Lines'

    config_id = fields.Many2one('form.extra.config', required=True)
    model_id = fields.Many2one('ir.model', string='Model')
    field_ids = fields.Many2many('ir.model.fields', string="Fields", domain="[('model_id','=',model_id)]")

class CrmLeadHeader(models.Model):
    _name = 'crm.lead.header'
    _description = 'Crm Lead Header'

    name = fields.Char(required=True)
    icon = fields.Binary()


class CrmLeadSidePanel(models.Model):
    _name = 'crm.lead.sidepanel'
    _description = 'Crm Lead SidePanel'
    _order = "sequence, name, id"

    name = fields.Char(required=True)
    sequence = fields.Integer('Sequence', default=1, help="Used to side panel stages. Lower is better.")
    parent_id = fields.Many2one('crm.lead.sidepanel')
    child_ids = fields.One2many('crm.lead.sidepanel', 'parent_id')
    header_ids = fields.Many2many('crm.lead.header')
    action_id = fields.Many2one('ir.actions.act_window', string='Action')
    extra_config_line_ids = fields.Many2many('form.extra.config.lines', string="Configurations", domain="[('model_id','=',model_id)]")
    model_id = fields.Many2one('ir.model', string='Model')
    icon = fields.Char(string="Icon")

    def _create_dynamic_pages(self):
        self.ensure_one()
        form_views = self.env['ir.ui.view'].sudo().search([('model','=like',self.model_id.model),('type','=','form'),('inherit_id','=',False)])
        for v in form_views:
            arch_tree = etree.fromstring(v.arch)
            node = arch_tree.find(".//notebook")
            page_path = [[k.attrib.get('string'), k] for k in arch_tree.findall(".//page") if k.attrib.get('name') not in ['internal_notes','extra','lead','site_details','application_details']]
            config_path = [pn.config_id.name for pn in self.extra_config_line_ids]
            rm_list = [x for x in page_path if x[0] not in config_path]
            for y in rm_list:
                node.remove(y[1])
            if node:
                for pn in self.extra_config_line_ids:
                    path = arch_tree.xpath("//page[@string='%s']" %pn.config_id.name)
                    if not path:
                        field_str = '<group><group>'
                        cnt = len(pn.field_ids)//2
                        for fl in pn.field_ids[:cnt]:
                            field_str += '<field name="%s"/>' %fl.name
                        if len(pn.field_ids)>=cnt:
                            field_str += '</group><group>'
                            for fl in pn.field_ids[cnt:]:
                                field_str += '<field name="%s"/>' %fl.name
                        field_str += '</group></group>'
                        page_string = '<page string="%s" >  %s </page>' % (pn.config_id.name, field_str)
                        add_node = etree.fromstring(page_string)
                        node.insert(0, add_node)
                v.sudo().write({'arch': etree.tostring(arch_tree, encoding='unicode')})

    def _create_dynamic_headers(self):
        self.ensure_one()
        form_views = self.env['ir.ui.view'].sudo().search([('model','=like',self.model_id.model),('type','=','form'),('inherit_id','=',False)])
        for v in form_views:
            arch_tree = etree.fromstring(v.arch)
            node = arch_tree.find(".//header")
            for n in arch_tree.xpath('//button[@name="dynamic_button"]'):
                n.getparent().remove(n)
            if node is not None:
                for pn in self.header_ids:
                    path = arch_tree.xpath("//button[@string='%s']" % (pn.name))
                    header_attrs="{'invisible':[('type','=','lead')]}"
                    if not path:
                        page_string = '<button name="dynamic_button" type="object" string="%s" class="oe_highlight"  attrs="%s"/>' % (pn.name, header_attrs)
                        add_node = etree.fromstring(page_string)
                        node.insert(0, add_node)
                v.sudo().write({'arch': etree.tostring(arch_tree, encoding='unicode')})

    @api.onchange('action_id', 'extra_config_line_ids', 'header_ids')
    def _onchange_action_id(self):
        self.ensure_one()
        if self.action_id and self.action_id.res_model:
            self.model_id = self.env['ir.model'].search([('model','=like',self.action_id.res_model)], limit=1).id
            self._create_dynamic_pages()
            self._create_dynamic_headers()
        else:
            self.model_id = False

class LeadTask(models.Model):
    _name = 'crm.lead.tasks'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Crm Lead Tasks'

    name = fields.Char(string="Name", required=True, tracking=True)
    due_date = fields.Datetime("Due By", tracking=True)
    assigned_to = fields.Many2one("res.users", string="Assigned To", tracking=True)
    assigned_by = fields.Many2one("res.users", string="Assigned By", tracking=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('in_progress', 'In-Progress'), ('done', 'Done'), ('cancel', 'Cancel')], string="State",
        default="draft", required=True, tracking=True)
    lead_id = fields.Many2one("crm.lead", string="Lead", required=True, tracking=True)
    task_id = fields.Char(string="Task ID", tracking=True)
    task_type = fields.Selection([('lead', 'lead'), ('opportunity', 'Opportunity')], string="Task Type", tracking=True)

    @api.model
    def create(self, values):
        crm_id = self.env['crm.lead'].sudo().browse(values.get('lead_id'))
        if crm_id.case_id:
            values['task_id'] = crm_id.case_id + "-" + self.env['ir.sequence'].next_by_code('task_generated_sequence')
        values['task_type'] = crm_id.type
        return super(LeadTask, self).create(values)


class LeadStakeholders(models.Model):
    _name = 'crm.lead.stakeholders'
    _description = 'Crm Lead Stakeholders'

    name = fields.Char(string="Name", required=True)
    photo = fields.Binary("Photo")
    lead_id = fields.Many2one("crm.lead", string="Lead", required=True)
    stakeholder_id = fields.Char(string="Stakeholder ID")

    @api.model
    def create(self, values):
        crm_id = self.env['crm.lead'].sudo().browse(values.get('lead_id'))
        values['stakeholder_id'] = crm_id.case_id + "-" + self.env['ir.sequence'].next_by_code(
            'stakeholder_generated_sequence')
        return super(LeadStakeholders, self).create(values)


class SecurityRequirement(models.Model):
    _name = 'security.requirement'
    _description = 'Crm Lead SecurityRequirement'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True, help="Set active to false to hide the Security Requirement without removing it.")

class Certainity(models.Model):
    _name = 'crm.certainity'
    _description = 'Crm Certainity'
    
    name = fields.Char(required=True)


class AppModeling(models.Model):
    _name = 'app.modeling'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Application Details'

    name = fields.Char(string="Application name", required=True, tracking=True)
    application_id = fields.Char(string="Application ID")
    application_hosted = fields.Selection([
        ('on_premise', 'On Premise'),
        ('public_cloud', 'Public Cloud'),
        ('msp', 'MSP'),
    ], string="Application Hosted", default="permise", required=True, tracking=True)
    ip_addr_fqdn = fields.Char(string="IP Address/Host Name/FQDN", tracking=True)
    port = fields.Char(string="Port")
    application_concurrent_users = fields.Char(string="Concurrent Users", tracking=True)
    per_session_bandwith = fields.Integer(string="Bandwidth per session", tracking=True)
    bandwidth_type = fields.Selection([
        ('kbps', 'Kbps'),
        ('mbps', 'Mbps'),
        ('gbps', 'Gbps')], string="Bandwidth Type", tracking=True)
    application_qos_parameter = fields.Selection([
        ('delay', 'Delay'),
        ('jitter','Jitter'),
        ('packet','Packet'),
    ], string="QoS Parameter", tracking=True)
    application_priority = fields.Selection([
        ('p1', 'P1'),
        ('p2', 'P2'),
        ('p3', 'P3'),
        ('p4', 'P4'),
    ], string="Priority for business", tracking=True)
    lead_id = fields.Many2one("crm.lead", string="Lead")
    active = fields.Boolean(default=True, help="Set active to false to hide the Application without removing it.")

    def _get_app_sequence(self,lead_id, application_hosted):
        if lead_id:
            crm_id = self.env['crm.lead'].sudo().browse(lead_id)
            app_hosted = {'on_premise': 'P','public_cloud': 'C','msp': 'M'}
            res = app_hosted.get(application_hosted) if application_hosted else ''
            if crm_id.partner_id:
                return crm_id.partner_id.name[:3] + str(self.env['ir.sequence'].next_by_code('application_details_sequence')) + res
        return False

    @api.model
    def create(self, values):
        values['application_id'] = self._get_app_sequence(values.get('lead_id'), values.get('application_hosted'))
        return super(AppModeling, self).create(values)

    def write(self, values):
        values['application_id'] = self._get_app_sequence(values.get('lead_id'), values.get('application_hosted'))
        return super(AppModeling, self).write(values)

    @api.constrains('name')
    def _check_name(self):
        for rec in self:
            c_name = self.env['app.modeling'].search([('name', '=ilike', rec.name), ('id', '!=', rec.id), ('lead_id', '=', rec.lead_id.id)])
            if c_name:
                raise ValidationError("Application Name already exists, please add unique name.")


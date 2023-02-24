# -*- coding: utf-8 -*-

from odoo import api, fields, models


class CreateTableWizard(models.TransientModel):
    _name = 'create.table.dynamic.wizard'
    _description = 'Create Table Wizard'

    name = fields.Char()
    description = fields.Char()

    def action_done_wizard(self):
        for rec in self:
            t_name = rec.name.lower().replace(" ", ".") 
            vals = {
                "name": rec.description,
                "model": 'x_'+ t_name,
                "order": 'id'
            }
            ir_model_obj = self.env['ir.model'].sudo()
            tbale_name = ir_model_obj.create(vals)

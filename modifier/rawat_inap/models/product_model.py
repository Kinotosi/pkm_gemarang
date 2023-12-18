from odoo import api, fields, models

class ProductProductModifier(models.Model):
    _inherit = 'product.product'

    insurance_ids = fields.Many2many(comodel_name='isurance.rawat.inap', string='Insurances')

class ProductTemplateModifier(models.Model):
    _inherit = 'product.template'

    insurance_ids = fields.Many2many(comodel_name='isurance.rawat.inap', string='Insurances')
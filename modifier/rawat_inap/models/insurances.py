from odoo import api, fields, models

class IsurancesRawatInap(models.Model):
    _name = "isurance.rawat.inap"
    _description = 'Isurance'

    name = fields.Char(string='Isurance', required=False)
    isurance_categ_id = fields.Many2one(comodel_name='isurance.category.rawat.inap', string='Isurance Category', required=False)
    is_active = fields.Boolean(string='Active', required=False)

class IsurancesCategoryRawatInap(models.Model):
    _name = 'isurance.category.rawat.inap'
    _description = 'Isurance Category'

    name = fields.Char(string='Isurance Category', required=True)
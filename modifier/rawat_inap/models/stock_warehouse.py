from odoo import api, fields, models

class StockWarehouseMod(models.Model):
    _inherit = 'stock.warehouse'

    is_virtual = fields.Boolean(string='Virtual Warehouse', required=False)
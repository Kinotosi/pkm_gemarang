from odoo import api, fields, models


class StockMoveLine(models.Model):
    _name = 'stock.move.input.output.line'
    _description = 'Stock Move Line'

    stock_input_move_id = fields.Many2one(comodel_name='stock.input.move', string='Stock Input Move', required=False)
    stock_out_move_id = fields.Many2one(comodel_name='stock.output.move', string='Stock Out Move', required=False)
    quantity = fields.Float(string='Quantity', required=False)
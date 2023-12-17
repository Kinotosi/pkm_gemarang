from odoo import api, fields, models

class StockNotification(models.TransientModel):
    _name = 'stock.notip.message'

    stock_input_id = fields.Many2one(comodel_name='stock.input', string='Stock Input', required=False)
    stock_input_move_ids = fields.Many2many(comodel_name='stock.input.move', string='Stock Input Move')
    stock_output_id = fields.Many2one(comodel_name='stock.output', string='Stock Output', required=False)
    stock_output_move_ids = fields.Many2many(comodel_name='stock.output.move', string='Stock Output Move')

    def action_confirm(self):
        if self.stock_input_id and self.stock_input_move_ids:
            for stock_move in self.stock_input_move_ids:
                stock_move.quantity_done = stock_move.demand_qty
            self.stock_input_id.action_done()

        if self.stock_output_id and self.stock_output_move_ids:
            for stock_move in self.stock_output_move_ids:
                stock_move.quantity_done = stock_move.demand_qty
            self.stock_output_id.action_done()
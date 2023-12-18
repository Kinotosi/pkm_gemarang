from odoo import api, fields, models, _
from odoo.exceptions import UserError

class StockCancel(models.TransientModel):
    _name = 'stock.cancel'

    stock_input_id = fields.Many2one(comodel_name='stock.input', string='Stock Input', required=False)
    stock_output_id = fields.Many2one(comodel_name='stock.output', string='Stock Output', required=False)
    reason_message = fields.Text(string="Reason", required=False)

    def action_confirm_cancel(self):
        stock_id = self.stock_input_id or self.stock_output_id
        if self.reason_message != '':
            stock_id.cancel_reason = self.reason_message
        else:
            raise UserError(_('Please, insert your Reason'))
        stock_id.write({'state': 'cancel'})

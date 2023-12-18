from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime

class ProductOrder(models.TransientModel):
    _name = 'product.patient.order'

    patient_id = fields.Many2one(comodel_name='patient.rawat.inap', string='Patient', required=False)
    source_location_id = fields.Many2one(comodel_name='stock.warehouse', string='Source Location', required=False)
    order_line_ids = fields.One2many(comodel_name='product.patient.order.line', inverse_name='product_order_id', string='Order Line', required=False)

    def action_confirm(self):
        check_order = self.order_line_ids.filtered(lambda x: x.onhand_qty <= 0.0)
        if check_order:
            raise UserError(_('Quantity on hand is lower than zero'))
        patient_vendor_id = self.env.ref('rawat_inap.patient_res_partner_id')
        delivery_order_data = {
            'vendor_id': patient_vendor_id.id,
            'source_location_id': self.source_location_id.id,
            'scheduled_date': datetime.now(),
            'source_document': self.patient_id.name,
            'patient_id': self.patient_id.id,
            'stock_output_move_ids': []
        }
        for line_id in self.order_line_ids:
            line_data = {
                'line_sequence': line_id.line_sequence,
                'product_id': line_id.product_id.id,
                'name': line_id.name,
                'demand_qty': line_id.quantity,
                'uom_id': line_id.uom_id.id
            }
            delivery_order_data['stock_output_move_ids'].append((0, 0, line_data))
        stock_out_id = self.env['stock.output'].create(delivery_order_data)
        stock_out_id.action_confirm_draft()
        stock_out_id.action_confirm()
        view_id = self.env.ref('rawat_inap.stock_output_view_form')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Delivery Orders'),
            'view_mode': 'form',
            'res_model': 'stock.output',
            'target': 'current',
            'res_id': stock_out_id.id,
            'views': [[view_id.id, 'form']],
        }

class ProductOrderLine(models.TransientModel):
    _name = 'product.patient.order.line'

    def default_get(self, fields_list):
        res = super(ProductOrderLine, self).default_get(fields_list)
        context_keys = self._context.keys()
        next_sequence = 1
        if 'order_line_ids' in context_keys:
            if len(self._context.get('order_line_ids')) > 0:
                next_sequence = len(self._context.get('order_line_ids')) + 1
        res.update({'line_sequence': next_sequence})
        return res

    line_sequence = fields.Integer(string='No.', required=False)
    product_id = fields.Many2one(comodel_name='product.product', string='Product', required=False)
    product_order_id = fields.Many2one(comodel_name='product.patient.order', string='Product Order', required=False)
    name = fields.Char(string='Description', required=False)
    quantity = fields.Float(string='Quantity', required=False)
    uom_id = fields.Many2one(comodel_name='uom.uom', string='Unit of Measure', required=False)
    source_location_id = fields.Many2one(comodel_name='stock.warehouse', string='Source Location', compute="_compute_source_location_id", store=True)
    onhand_qty = fields.Float(string='Quantity On Hand', compute='_compute_onhand_qty')
    unit_price = fields.Float(string='Unit Price', compute='_compute_product_id', store=True)
    total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount', store=True)

    @api.depends('product_id')
    def _compute_onhand_qty(self):
        for rec in self:
            if rec.product_id:
                stock_move_input = self.env['stock.input.move'].search(
                    [('product_id', '=', rec.product_id.id), ('use_qty', '>', 0.0),
                     ('dest_location_id', '=', rec.source_location_id.id), ('state', '=', 'done')])
            else:
                stock_move_input = False
            if stock_move_input:
                rec.onhand_qty = sum([move_id.use_qty for move_id in stock_move_input])
            else:
                rec.onhand_qty = 0.0

    @api.depends('product_order_id.source_location_id')
    def _compute_source_location_id(self):
        for rec in self:
            if rec.product_order_id.source_location_id:
                rec.source_location_id = rec.product_order_id.source_location_id.id
            else:
                rec.source_location_id = False

    @api.onchange('product_id')
    def get_uom(self):
        for rec in self:
            if rec.product_id:
                rec.uom_id = rec.product_id.uom_id.id
                rec.name = rec.product_id.name

    @api.depends('product_id')
    def _compute_product_id(self):
        for rec in self:
            if rec.product_id:
                rec.uom_id = rec.product_id.uom_id.id
                rec.unit_price = rec.product_id.list_price
            else:
                rec.uom_id = False
                rec.unit_price = 0.0

    @api.depends('product_id', 'unit_price', 'quantity')
    def _compute_total_amount(self):
        for rec in self:
            if rec.product_id:
                rec.total_amount = rec.unit_price * rec.quantity
            else:
                rec.total_amount = 0.0
from odoo import api, fields, models, _

class StockOutput(models.Model):
    _name = "stock.output"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Stock Output"

    name = fields.Char(string='Name', required=False)
    state = fields.Selection(string='State',
        selection=[
            ('draft', 'Draft'), ('confirmed', 'Waiting'), ('assigned', 'Ready'), ('done', 'Done'), ('cancel', 'Canceled')
        ],
        required=False, default='draft', tracking=True )

    vendor_id = fields.Many2one(comodel_name='res.partner', string='Vendor', required=False)
    source_location_id = fields.Many2one(comodel_name='stock.warehouse', string='Source Location', required=False)
    dest_location_id = fields.Many2one(comodel_name='stock.warehouse', string='Destination Location', required=False, default=lambda self: self.env.ref('rawat_inap.ir_stock_output_data'))
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=False, default=lambda self: self.env.company)
    date_done = fields.Datetime(string='Date of Transfer', required=False)
    scheduled_date = fields.Datetime(string='Scheduled Date', required=False)
    stock_output_move_ids = fields.One2many(comodel_name='stock.output.move', inverse_name='stock_output_id', string='Stock Move', required=False)
    source_document = fields.Char(string='Source Document', required=False)
    patient_id = fields.Many2one(comodel_name='patient.rawat.inap', string='Patient', required=False)
    cancel_reason = fields.Text(string="Cancel Reason", required=False)
    note = fields.Text(string="Note", required=False)

    def action_confirm_draft(self):
        for rec in self:
            rec.state = 'confirmed'

    def action_confirm(self):
        for rec in self:
            rec.state = 'assigned'

    def action_set_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_check_done(self):
        for rec in self:
            order_ids = rec.stock_output_move_ids.filtered(lambda x: x.demand_qty > 0.0 and x.quantity_done == 0.0)
            if order_ids:
                stock_notip_id = self.env.ref('rawat_inap.stock_notip_message_view_form')
                return {
                    'name': _('Immediate Transfer'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'stock.notip.message',
                    'view_mode': 'form',
                    'views': [(stock_notip_id.id, 'form')],
                    'view_id': stock_notip_id.id,
                    'target': 'new',
                    'context': {
                        'default_stock_output_id': rec.id,
                        'default_stock_output_move_ids': [(6, 0, order_ids.ids)]
                    }
                }
            else:
                rec.action_done()

    def action_done(self):
        for rec in self:
            for produc_id in rec.stock_output_move_ids:
                if produc_id.quantity_done > produc_id.onhand_qty:
                    produc_id.quantity_done = produc_id.onhand_qty
                stock_move_input = self.env['stock.input.move'].search([('product_id', '=', produc_id.product_id.id), ('use_qty', '>', 0.0), ('dest_location_id', '=', produc_id.source_location_id.id), ('state', '=', 'done')])
                if stock_move_input:
                    qty_done = produc_id.quantity_done
                    use_qty = sum(stock_move_input.mapped('use_qty'))
                    for stock_move in stock_move_input:
                        if qty_done > stock_move.use_qty:
                            stock_move_line = self.env['stock.move.input.output.line'].create({
                                'stock_input_move_id': stock_move.id,
                                'stock_out_move_id': produc_id.id,
                                'quantity': stock_move.use_qty,
                            })
                            qty_done -= stock_move.use_qty
                            stock_move._compute_use_qty()
                        else:
                            stock_move_line = self.env['stock.move.input.output.line'].create({
                                'stock_input_move_id': stock_move.id,
                                'stock_out_move_id': produc_id.id,
                                'quantity': qty_done,
                            })
                            stock_move._compute_use_qty()
                            break
                else:
                    produc_id.quantity_done = 0.0
            if rec.patient_id:
                for move_id in rec.stock_output_move_ids:
                    order_id = self.env['patient.order.line'].search([('product_id','=',move_id.product_id.id),('patient_id','=',rec.patient_id.id)], limit=1)
                    if order_id:
                        order_id.write({'quantity': order_id.quantity + move_id.quantity_done})
                    else:
                        self.env['patient.order.line'].create({
                            'line_sequence': len(rec.patient_id.order_line) + 1,
                            'product_id': move_id.product_id.id,
                            'patient_id': rec.patient_id.id,
                            'name': move_id.name,
                            'quantity': move_id.quantity_done,
                        })

            rec.state = 'done'

    def action_cancel(self):
        for rec in self:
            stock_cancel_view_id = self.env.ref('rawat_inap.stock_cancel_view_form')
            return {
                'name': _('Cancel Stock'),
                'type': 'ir.actions.act_window',
                'res_model': 'stock.cancel',
                'view_mode': 'form',
                'views': [(stock_cancel_view_id.id, 'form')],
                'view_id': stock_cancel_view_id.id,
                'target': 'new',
                'context': {
                    'default_stock_output_id': rec.id
                }
            }

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            get_sequence = self.env['ir.sequence'].next_by_code('stock.output.rawat.inap')
            if get_sequence:
                vals['name'] = get_sequence
        return super(StockOutput, self).create(vals)

class StockOutputMove(models.Model):
    _name = "stock.output.move"
    _description = "Stock Output Move"

    def default_get(self, fields_list):
        res = super(StockOutputMove, self).default_get(fields_list)
        context_keys = self._context.keys()
        next_sequence = 1
        if 'stock_output_move_ids' in context_keys:
            if len(self._context.get('stock_output_move_ids')) > 0:
                next_sequence = len(self._context.get('stock_output_move_ids')) + 1
        res.update({'line_sequence': next_sequence})
        return res

    line_sequence = fields.Integer(string='No.', required=False)
    product_id = fields.Many2one(comodel_name='product.product', string='Product', required=False)
    stock_output_id = fields.Many2one(comodel_name='stock.output', string='Stock Output', required=False)
    state = fields.Selection(related='stock_output_id.state')
    name = fields.Char(string='Description', required=False)
    demand_qty = fields.Float(string='Demand', required=False)
    quantity_done = fields.Float(string='Done', required=False)
    remaining_qty = fields.Float(string='Remaining', compute='_compute_remaining_qty')
    uom_id = fields.Many2one(comodel_name='uom.uom', string='Unit of Measure', required=False)
    source_location_id = fields.Many2one(comodel_name='stock.warehouse', string='Source Location', compute="_compute_source_location_id", store=True, readonly=False)
    onhand_qty = fields.Float(string='Quantity On Hand', compute='_compute_onhand_qty')

    @api.depends('product_id')
    def _compute_onhand_qty(self):
        for rec in self:
            if rec.product_id:
                stock_move_input = self.env['stock.input.move'].search([('product_id','=',rec.product_id.id), ('use_qty','>',0.0), ('dest_location_id','=',rec.source_location_id.id), ('state','=','done')])
            else:
                stock_move_input = False
            if stock_move_input:
                rec.onhand_qty = sum([move_id.use_qty for move_id in stock_move_input])
            else:
                rec.onhand_qty = 0.0

    @api.depends('stock_output_id.source_location_id')
    def _compute_source_location_id(self):
        for rec in self:
            if rec.stock_output_id.source_location_id:
                rec.source_location_id = rec.stock_output_id.source_location_id.id
            else:
                rec.source_location_id = False

    @api.depends('demand_qty', 'quantity_done')
    def _compute_remaining_qty(self):
        for rec in self:
            rec.remaining_qty = rec.demand_qty - rec.quantity_done

    @api.onchange('product_id')
    def get_uom(self):
        for rec in self:
            if rec.product_id:
                rec.uom_id = rec.product_id.uom_id.id

    @api.onchange('product_id')
    def get_name(self):
        for rec in self:
            if rec.product_id:
                rec.name = rec.product_id.name

from odoo import api, fields, models, _

class StockInput(models.Model):
    _name = "stock.input"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Stock Input"

    name = fields.Char(string='Name', required=False)
    state = fields.Selection(string='State',
        selection=[
            ('draft', 'Draft'), ('confirmed', 'Waiting'), ('assigned', 'Ready'), ('done', 'Done'), ('cancel', 'Canceled')
        ],
        required=False, default='draft', tracking=True )

    vendor_id = fields.Many2one(comodel_name='res.partner', string='Vendor', required=False)
    source_location_id = fields.Many2one(comodel_name='stock.warehouse', string='Source Location', required=False, default=lambda self: self.env.ref('rawat_inap.ir_stock_input_data'))
    dest_location_id = fields.Many2one(comodel_name='stock.warehouse', string='Destination Location', required=False)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=False, default=lambda self: self.env.company)
    date_done = fields.Datetime(string='Date of Transfer', required=False)
    scheduled_date = fields.Datetime(string='Scheduled Date', required=False)
    stock_input_move_ids = fields.One2many(comodel_name='stock.input.move', inverse_name='stock_input_id', string='Stock Move', required=False)
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
            order_ids = rec.stock_input_move_ids.filtered(lambda x: x.demand_qty > 0.0 and x.quantity_done == 0.0)
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
                        'default_stock_input_id': rec.id,
                        'default_stock_input_move_ids': [(6, 0, order_ids.ids)]
                    }
                }
            else:
                rec.action_done()

    def action_done(self):
        for rec in self:

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
                    'default_stock_input_id': rec.id
                }
            }

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            get_sequence = self.env['ir.sequence'].next_by_code('stock.input.rawat.inap')
            if get_sequence:
                vals['name'] = get_sequence
        return super(StockInput, self).create(vals)

class StockInputMove(models.Model):
    _name = "stock.input.move"
    _description = "Stock Input Move"

    def default_get(self, fields_list):
        res = super(StockInputMove, self).default_get(fields_list)
        context_keys = self._context.keys()
        next_sequence = 1
        if 'stock_input_move_ids' in context_keys:
            if len(self._context.get('stock_input_move_ids')) > 0:
                next_sequence = len(self._context.get('stock_input_move_ids')) + 1
        res.update({'line_sequence': next_sequence})
        return res

    line_sequence = fields.Integer(string='No.', required=False)
    product_id = fields.Many2one(comodel_name='product.product', string='Product', required=False)
    stock_input_id = fields.Many2one(comodel_name='stock.input', string='Stock Input', required=False)
    state = fields.Selection(related='stock_input_id.state')
    name = fields.Char(string='Description', required=False)
    demand_qty = fields.Float(string='Demand', required=False)
    quantity_done = fields.Float(string='Done', required=False)
    remaining_qty = fields.Float(string='Remaining', compute='_compute_remaining_qty')
    uom_id = fields.Many2one(comodel_name='uom.uom', string='Unit of Measure', required=False)
    dest_location_id = fields.Many2one(comodel_name='stock.warehouse', string='Destination Location', compute="_compute_dest_location_id", store=True)
    stock_move_line_ids = fields.One2many(comodel_name='stock.move.input.output.line', inverse_name='stock_input_move_id', string='Stock Move Line', required=False)
    use_qty = fields.Float(string='Use Quantity', compute="_compute_use_qty", store=True)

    @api.depends('stock_move_line_ids', 'stock_move_line_ids.quantity', 'state')
    def _compute_use_qty(self):
        for rec in self:
            if rec.stock_move_line_ids:
                rec.use_qty = rec.quantity_done - sum(rec.stock_move_line_ids.mapped('quantity'))
            else:
                rec.use_qty = rec.quantity_done

            moveout_ids = self.env['stock.output.move'].search([('state','!=','done'), ('product_id','=',rec.product_id.id)])
            if moveout_ids and rec.state == 'done':
                for moveout_id in moveout_ids:
                    moveout_id._compute_onhand_qty()

    @api.depends('stock_input_id.dest_location_id')
    def _compute_dest_location_id(self):
        for rec in self:
            if rec.stock_input_id.dest_location_id:
                rec.dest_location_id = rec.stock_input_id.dest_location_id.id
            else:
                rec.dest_location_id = False

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


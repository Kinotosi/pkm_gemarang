from odoo import api, fields, models, _
from datetime import datetime

class PatientRawatInap(models.Model):
    _name = 'patient.rawat.inap'
    _description = 'Patient Rawat Inap'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=False, tracking=True)
    state = fields.Selection(string='State',
        selection=[
            ('draft', 'Draft'), ('verification', 'Verification'), ('inpatient', 'Inpatient'), ('done', 'Done'), ('cancel', 'Cancel')
        ],
        required=False, default='draft', tracking=True)

    street = fields.Char(string='Street', required=False, tracking=True)
    street2 = fields.Char(string='Street2', required=False)
    city = fields.Char(string='City', required=False, tracking=True)
    state_id = fields.Many2one(comodel_name='res.country.state', string='State', required=False)
    zip = fields.Char(string='Zip', required=False)
    country_id = fields.Many2one(comodel_name='res.country', string='Country', required=False, tracking=True)
    id_patient = fields.Char(string='ID Patient', required=False, tracking=True)
    start_date = fields.Datetime(string='Start Date', required=False)
    end_date = fields.Datetime(string='End Date', required=False)
    phone = fields.Char(string='Phone', required=False)
    mobile = fields.Char(string='Mobile', required=False)
    email = fields.Char(string='Email', required=False)
    is_insurance = fields.Boolean(string='Insurance', required=False, tracking=True)
    id_insurance = fields.Char(string='ID Insurance', required=False, tracking=True)
    insurance_id = fields.Many2one(comodel_name='isurance.rawat.inap',string='Add Insurance', required=False, tracking=True)
    room_id = fields.Many2one(comodel_name='rooms.rawat.inap', string='Room', required=False, tracking=True)
    filter_room_ids = fields.Many2many(comodel_name='rooms.rawat.inap', string='Filter Room', compute='_compute_filter_room')
    currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', required=False, default=lambda self: self.env.user.company_id.currency_id.id)
    cancel_reason = fields.Text(string="Cancel Reason", required=False)
    note = fields.Text(string="Note", required=False)
    order_line = fields.One2many(comodel_name='patient.order.line', inverse_name='patient_id', string='Order Line', required=False)
    stock_out_count = fields.Integer(string='Stock Out Count', compute='_compute_stock_out_count')

    amount_subtotal = fields.Float(string='Subtotal', compute='_compute_amount', store=True)
    amount_discount = fields.Float(string='-Discount', compute='_compute_amount', store=True)
    amount_total = fields.Float(string='Total', compute='_compute_amount', store=True)

    def _compute_stock_out_count(self):
        for rec in self:
            stock_out_ids = self.env['stock.output'].search([('patient_id','=',rec.id),('state','!=','cancel')])
            if stock_out_ids:
                rec.stock_out_count = len(stock_out_ids.ids)
            else:
                rec.stock_out_count = 0

    def action_open_delivery_orders(self):
        for rec in self:
            if rec.stock_out_count >= 1:
                stock_out_ids = self.env['stock.output'].search([('patient_id', '=', rec.id),('state','!=','cancel')])
                view_form_id = self.env.ref('rawat_inap.stock_output_view_form')
                view_tree_id = self.env.ref('rawat_inap.stock_output_view_tree')
                return {
                    'type': 'ir.actions.act_window',
                    'name': _('Delivery Orders'),
                    'view_mode': 'tree,form',
                    'res_model': 'stock.output',
                    'target': 'current',
                    'domain': [('id','in',stock_out_ids.ids)],
                    'views': [[view_tree_id.id, 'tree'], [view_form_id.id, 'form']],
                }

    @api.depends('room_id', 'order_line', 'order_line.total_amount', 'is_insurance', 'insurance_id')
    def _compute_amount(self):
        for rec in self:
            subtotal = 0.0
            discount = 0.0
            total = 0.0

            if rec.room_id:
                subtotal += rec.room_id.list_price

            if rec.order_line:
                for order_id in rec.order_line:
                    subtotal += order_id.total_amount

            if rec.is_insurance and rec.insurance_id:
                if rec.insurance_id.id in rec.room_id.isurance_categ_ids.ids:
                    discount += rec.room_id.list_price
                for order_id in rec.order_line:
                    if rec.insurance_id.id in order_id.product_id.insurance_ids.ids:
                        discount += order_id.total_amount

            total += subtotal - discount

            rec.amount_subtotal = subtotal
            rec.amount_discount = discount
            rec.amount_total = total

    @api.depends('is_insurance', 'insurance_id')
    def _compute_filter_room(self):
        for rec in self:
            domain = []
            if rec.is_insurance and rec.insurance_id:
                domain.append(('isurance_categ_ids','in',[rec.insurance_id.id]))
            room_ids = self.env['rooms.rawat.inap'].search(domain)
            if room_ids:
                rec.filter_room_ids = [(6, 0, room_ids.ids)]
            else:
                rec.filter_room_ids = [(6, 0, [])]

    def action_draft_confirm(self):
        for rec in self:
            rec.state = 'verification'

    def action_verication_confirm(self):
        for rec in self:
            rec.start_date = datetime.now()
            rec.state = 'inpatient'

    def action_set_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def action_add_product(self):
        add_product_id = self.env.ref('rawat_inap.product_patient_order_view_form')
        return {
            'name': _('Add Product'),
            'type': 'ir.actions.act_window',
            'res_model': 'product.patient.order',
            'view_mode': 'form',
            'views': [(add_product_id.id, 'form')],
            'view_id': add_product_id.id,
            'target': 'new',
            'context': {
                'default_patient_id': self.id
            }
        }
class PatientOrderLine(models.Model):
    _name = 'patient.order.line'
    _description = 'Order Line'

    def default_get(self, fields_list):
        res = super(PatientOrderLine, self).default_get(fields_list)
        context_keys = self._context.keys()
        next_sequence = 1
        if 'order_line' in context_keys:
            if len(self._context.get('order_line')) > 0:
                next_sequence = len(self._context.get('order_line')) + 1
        res.update({'line_sequence': next_sequence})
        return res

    line_sequence = fields.Integer(string='No.', required=False)
    product_id = fields.Many2one(comodel_name='product.product', string='Product', required=False)
    patient_id = fields.Many2one(comodel_name='patient.rawat.inap', string='Patient', required=False)
    state = fields.Selection(related='patient_id.state')
    name = fields.Char(string='Description', required=False)
    quantity = fields.Float(string='Quantity', required=False)
    uom_id = fields.Many2one(comodel_name='uom.uom', string='Unit of Measure', compute='_compute_product_id', store=True)
    unit_price = fields.Float(string='Unit Price', compute='_compute_product_id', store=True)
    total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount', store=True)

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




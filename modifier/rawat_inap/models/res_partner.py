from odoo import api, fields, models

class ResPartnerModifier(models.Model):
    _inherit = 'res.partner'

    employee_type = fields.Selection(string='Type', selection=[('doctor', 'Doctor'), ('nurse', 'Nurse')], required=False, default='doctor')
    is_rawat_inap = fields.Boolean(string='Rawat Inap', required=False)
    is_vendor = fields.Boolean(string='Vendor', required=False)

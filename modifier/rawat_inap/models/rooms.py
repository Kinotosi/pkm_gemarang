from odoo import api, fields, models

class RoomsRawatInap(models.Model):
    _name = "rooms.rawat.inap"
    _description = 'Rooms'

    name = fields.Char(string='Room', required=False)
    isurance_categ_ids = fields.Many2many(comodel_name='isurance.rawat.inap', string='Isurance', required=False)
    room_tye = fields.Many2one(comodel_name='rooms.type.rawat.inap', string='Type',required=False)
    is_active = fields.Boolean(string='Active', required=False)

class RoomsTypeRawatInap(models.Model):
    _name = 'rooms.type.rawat.inap'
    _description = 'Rooms Type'

    name = fields.Char(string='Room Type', required=True)
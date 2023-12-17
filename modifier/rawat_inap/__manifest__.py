# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Rawat Inap - PKM Gemarang',
    'author': 'Arga Dwi Ardinata',
    'category': '',
    'version': '14.0.1.1.0',
    'description': '',
    'summary': 'Odoo 14 Purchase',
    'sequence': 10,
    'website': '',
    'depends': ['base', 'account', 'l10n_id_efaktur', 'stock'],
    'license': 'LGPL-3',
    'demo': [],
    'data': [
        'security/ir.model.access.csv',

        'data/ir_sequence.xml',
        'data/stock_warehouse_data.xml',

        'views/res_partner_views.xml',
        'views/product_views.xml',
        'views/stock_input_views.xml',
        'views/stock_output_views.xml',
        'views/stock_move_line.xml',
        'views/isurances_views.xml',
        'views/menuitem_view.xml',

        'wizard/stock_notification_views.xml',
        'wizard/stock_cancel_views.xml',
    ],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
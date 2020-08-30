# -*- encoding: utf-8 -*-
{
    'name': 'Kardex Valorizado',
    'version': '1.0',
    'author': 'ing. Jean Paul Casis',
    'website': 'www.pvodoo.com',
    'category': 'account',
    'depends': ['product','stock','account','jp_foreign_trade_logistics','mrp'],
    'description': """KARDEX VALORIZADO""",
    'demo': [],
    'data': [
        'security/ir.model.access.csv',
        'report/landed_cost_report_templates.xml',
        'report/landed_cost_report.xml',
        'views/account_move.xml',
        'views/stock_picking_views.xml',
        # 'views/stock_landed_cost.xml',
        'views/stock_inventory.xml',
        'views/stock_valuation_layer.xml',
        'wizard/make_kardex_view.xml',
        'views/product.xml',
        'data/tipo.xml',
    ],
    'auto_install': False,
    'installable': True
}

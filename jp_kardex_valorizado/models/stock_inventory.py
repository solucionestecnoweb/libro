# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    is_initial = fields.Boolean(string='Is Initial?')

class StockInventoryLine(models.Model):
    _inherit = 'stock.inventory.line'

    initial_cost = fields.Float(string='Initial Cost', digits=(12, 8))
    is_initial = fields.Boolean(store=True, related='inventory_id.is_initial',string='Is Initial?')


class StockValuationLayer(models.Model):

    _inherit = 'stock.valuation.layer'

    # Adicional de digitos al campo (8)
    unit_cost = fields.Float('Unit Value', readonly=True, digits=(12,8))
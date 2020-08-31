# -*- coding: utf-8 -*-

from collections import namedtuple
import json
import time
from odoo import api, fields, models, _ , exceptions


class type_operation_kardex(models.Model):
    _name = 'type.operation.kardex'

    name = fields.Char('Nombre')
    code = fields.Char('Codigo')


class StockPicking(models.Model):
    _inherit = "stock.picking"

    kardex_date = fields.Datetime(string='Fecha kardex', readonly=False, default=fields.Datetime.now)
    use_kardex_date = fields.Boolean('Usar Fecha kardex',default=True)
    invoice_id = fields.Many2one('account.move', string='Invoice')
    type_operation_sunat_id = fields.Many2one('type.operation.kardex','Tipo de Transacción')
    
    @api.constrains('picking_type_id', 'state')
    def set_type_operation_sunat_id(self):
        if self.picking_type_id.id :
            self.type_operation_sunat_id = self.picking_type_id.type_operation_sunat_id
            

class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    type_operation_sunat_id = fields.Many2one('type.operation.kardex','Tipo de Transacción')

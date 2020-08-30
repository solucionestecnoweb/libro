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

	@api.onchange('invoice_id')
	def _onchange_invoice_id(self):
		if self.invoice_id.id.origin:
			invoice_id = self.invoice_id.id.origin
		else:
			invoice_id = self.invoice_id.id
		sm = self.env['stock.move'].search([('picking_id','=', self.id.origin)])
		if self.invoice_id and self.invoice_id.type_document_id.code == '01':
			am = self.env['account.move'].search([('id','=', invoice_id)])
			for move in sm:
				aml = self.env['account.move.line'].search([('move_id','=', am.id),('product_id','=', move.product_id.id)])
				svl = self.env['stock.valuation.layer'].search([('stock_move_id','=',move.id)])
				if am.currency_id != self.env.user.company_id.currency_id:
					if am.tc_per:
						svl.unit_cost = (aml.price_total / aml.quantity) * am.currency_rate
					else:
						rate = am.currency_id._get_conversion_rate(am.currency_id, self.env.user.company_id.currency_id, self.env.user.company_id, am.invoice_date)
						svl.unit_cost = (aml.price_total / aml.quantity) * rate
				else:
					svl.unit_cost = aml.price_unit
		else:
			for move in sm:
				svl = self.env['stock.valuation.layer'].search([('stock_move_id','=',move.id)])
				if move.purchase_line_id:
					if move.purchase_line_id.currency_id != self.env.user.company_id.currency_id:
						if move.picking_id.use_kardex_date:
							rate = move.purchase_line_id.currency_id._get_conversion_rate(move.purchase_line_id.currency_id, self.env.user.company_id.currency_id, self.env.user.company_id, move.picking_id.kardex_date)
						else:
							rate = move.purchase_line_id.currency_id._get_conversion_rate(move.purchase_line_id.currency_id, self.env.user.company_id.currency_id, self.env.user.company_id, move.picking_id.scheduled_date)
						svl.unit_cost = (move.purchase_line_id.price_total / move.purchase_line_id.product_qty) * rate
					else:
						svl.unit_cost = (move.purchase_line_id.price_total / move.purchase_line_id.product_qty)
				else:
					if move.origin_returned_move_id:
						svl_origin = self.env['stock.valuation.layer'].search([('stock_move_id','=',move.origin_returned_move_id.id)])
						svl.unit_cost = svl_origin.unit_cost


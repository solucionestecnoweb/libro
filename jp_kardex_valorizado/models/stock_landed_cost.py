# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class LandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    vendor_bill_ids = fields.Many2many('account.move', string='Vendor bills')

    def button_validate(self):
        res = super(LandedCost, self).button_validate()
        stock_moves = self.env['stock.move'].search([('picking_id','in',self.picking_ids.ids)])
        # stock_moves.kardex_price_unit = 0
        for move in stock_moves:
            move.kardex_price_unit += self.amount_total / sum(stock_moves.mapped('product_uom_qty'))
        # stock_moves = self.env['stock.move'].search([('picking_id','in',self.picking_ids.ids)])
        # landed_costs = self.env['stock.landed.cost'].search([('picking_ids','in',self.picking_ids.ids)])
        # stock_moves.kardex_price_unit = 0
        # for move in stock_moves:
        #     for cost in landed_costs:
        #         for line in cost.valuation_adjustment_lines:
        #             if move.id == line.move_id.id and move.product_id == line.product_id:
        #                 move.kardex_price_unit += line.additional_landed_cost / line.quantity
        return res

    # def button_revalidate(self):
    #     stock_moves = self.env['stock.move'].search([('picking_id','in',self.picking_ids.ids)])
    #     # landed_costs = self.env['stock.landed.cost'].search([('picking_ids','in',self.picking_ids.ids)])
    #     stock_moves.kardex_price_unit = 0
    #     for move in stock_moves:
    #         # for cost in landed_costs:
    #             print(sum(stock_moves.mapped('product_uom_qty')))
    #             move.kardex_price_unit += self.amount_total / sum(stock_moves.mapped('product_uom_qty'))
    #             # for line in cost.valuation_adjustment_lines:
    #             #     if move.id == line.move_id.id and move.product_id == line.product_id:
    #             #         move.kardex_price_unit += line.additional_landed_cost / line.quantity
    #             #         print(str(line.additional_landed_cost) + '/' + str(line.quantity) + '=' + str(line.additional_landed_cost / line.quantity))
    #                     # print(move.kardex_price_unit)

    # @api.onchange('vendor_bill_ids')
    # def _onchange_vendor_bill_ids(self):
    def populate_vendor_bill_ids(self):
        if self.vendor_bill_ids:
            vals = []
            for bill in self.vendor_bill_ids:
                for item in bill.invoice_line_ids:
                    tax_total = 0
                    for tax in item.tax_ids:
                        tax_total += item.price_subtotal * (tax.amount/100)
                    val = {
                        'cost_id': self.id,
                        'product_id': item.product_id.id,
                        'name': item.name,
                        'account_id': item.account_id.id,
                        'price_unit': item.price_total,
                        'split_method': 'equal'
                    }
                    vals.append(val)
            self.cost_lines.unlink()
            self.env['stock.landed.cost.lines'].create(vals)
        # return True
    
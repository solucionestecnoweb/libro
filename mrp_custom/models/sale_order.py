from odoo import _, fields, models, api
from odoo.exceptions import AccessError, UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    production_ids = fields.Many2many('mrp.production', copy=False)
    production_count = fields.Integer(compute="count_production", string="Productions")

    def count_production(self):
        production = []
        number = 0
        for record in self.production_ids:
            production += [record.id]
        if self.production_ids:
            query = 'select count(id) from mrp_production where id in'
            string_production = (str(production).replace('[', '(').replace(']', ')'))
            query_execute = query + string_production
            self._cr.execute(query_execute)
            value = self._cr.fetchall()
            for count in value:
                number = count[0]
        self['production_count'] = number

    def call_production(self):
        action = self.env.ref('mrp.mrp_production_action').read()[0]
        production = []
        for record in self.production_ids:
            production += [record.id]
        (str(production).replace('[', '(').replace(']', ')'))
        action['domain'] = [('id', 'in', production)]
        return action

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        productions = []
        for lines in self.order_line:
            if lines.product_id.generate_production:
                if lines.product_id.bom_ids:
                    bom = []
                    for bom_id in lines.product_id.bom_ids:
                        if not bom:
                            bom = bom_id

                    if bom.routing_id:
                        if bom.routing_id.capacity_batch > 0:
                            qty_loop = lines.product_uom_qty

                            while qty_loop > 0:
                                if qty_loop > bom.routing_id.capacity_batch:
                                    qty_to_produce = bom.routing_id.capacity_batch
                                else:
                                    qty_to_produce = qty_loop

                                if self.warehouse_id.manu_type_id.active:
                                    production = self.create_production(str(self.name),
                                                                        lines.product_id.id,
                                                                        lines.product_id.product_tmpl_id.id,
                                                                        lines.product_uom.id,
                                                                        qty_to_produce,
                                                                        bom.id,
                                                                        self.warehouse_id.manu_type_id.id,
                                                                        self.warehouse_id.manu_type_id.default_location_src_id.id,
                                                                        self.warehouse_id.manu_type_id.default_location_dest_id.id)
                                    qty_loop -= qty_to_produce
                                    productions += [production.id]
                                    production._onchange_move_raw()
                                    production.action_confirm()
                                else:
                                    raise ValidationError(_(
                                        'The type of manufacturing operation of this warehouse is archived, please choose another warehouse or un-archive the type of operation and re-process'))
                        else:
                            raise ValidationError(_(
                                'You must configure the maximum capacity to produce per work route, please validate'))
                    else:
                        if self.warehouse_id.manu_type_id.active:
                            production = self.create_production(str(self.name),
                                                                                      lines.product_id.id,
                                                                                      lines.product_id.product_tmpl_id.id,
                                                                                      lines.product_uom.id,
                                                                                      lines.product_uom_qty,
                                                                                      bom.id,
                                                                                      self.warehouse_id.manu_type_id.id,
                                                                                      self.warehouse_id.manu_type_id.default_location_src_id.id,
                                                                                      self.warehouse_id.manu_type_id.default_location_dest_id.id)
                            productions += [production.id]
                            production._onchange_move_raw()
                            production.action_confirm()

                        else:
                            raise ValidationError(_(
                                'The type of manufacturing operation of this warehouse is archived, please choose another warehouse or un-archive the type of operation and re-process'))

                    self.production_ids = productions
        return res

    def create_production(self, name, product_id, product_tmpl_id, product_uom_id, product_qty, bom_id, picking_type_id,
                          location_src_id, location_dest_id):
        production = self.env['mrp.production'].create({'origin': name,
                                                        'state': 'draft',
                                                        'product_id': product_id,
                                                        'product_tmpl_id': product_tmpl_id,
                                                        'product_uom_id': product_uom_id,
                                                        'product_qty': product_qty,
                                                        'bom_id': bom_id,
                                                        'picking_type_id': picking_type_id,
                                                        'location_src_id': location_src_id,
                                                        'location_dest_id': location_dest_id})
        return production


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_uom_qty')
    def validate_qty_production(self):
        for lines in self:
            number_max = 10
            if lines.product_id.bom_ids:
                bom = []
                for bom_id in lines.product_id.bom_ids:
                    if not bom:
                        bom = bom_id

                if bom.routing_id:
                    if bom.routing_id.capacity_batch > 0:
                        qty_loop = lines.product_uom_qty
                        turns_qty = 0
                        while qty_loop > 0:
                            if qty_loop > bom.product_qty:
                                qty_to_produce = bom.routing_id.capacity_batch
                                turns_qty += 1
                            else:
                                qty_to_produce = qty_loop
                                turns_qty += 1

                            qty_loop -= qty_to_produce

                        if turns_qty >= number_max:
                            message = _('Ten precaucion, el producto a vender generará: %s producciones' % (
                                str(turns_qty)))
                            mess = {'title': _('Warning production!'),
                                    'message': message
                                    }
                            return {'warning': mess}

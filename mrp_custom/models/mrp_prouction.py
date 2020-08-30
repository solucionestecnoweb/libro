from odoo import fields, models, api


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    processed_picking_list = fields.Char()
    pick_ids = fields.Many2many('stock.picking', copy=False)
    picks_count = fields.Integer(compute="count_pick", copy=False, string="Picks")

    def count_pick(self):
        picks = []
        number = 0
        for record in self.pick_ids:
            picks += [record.id]
        if self.pick_ids:
            query = 'select count(id) from stock_picking where id in'
            string_picks = (str(picks).replace('[', '(').replace(']', ')'))
            query_execute = query + string_picks
            self._cr.execute(query_execute)
            value = self._cr.fetchall()
            for count in value:
                number = count[0]
        self['picks_count'] = number

    def call_picks(self):
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        picks = []
        for record in self.pick_ids:
            picks += [record.id]
        (str(picks).replace('[', '(').replace(']', ')'))
        action['domain'] = [('id', 'in', picks)]
        return action


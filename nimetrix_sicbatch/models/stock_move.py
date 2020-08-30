import sys

from odoo import fields, models, api, _

from . import sql_connection
from . import utils
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_done(self):
        res = super(StockPicking, self).action_done()
        for record in self:
            lines = self.env['stock.move.line'].search([
                ('picking_id', '=', record.id)
            ])
            for line in lines:
                if line.product_id.product_tmpl_id.categ_id.send_sicbatch and line.picking_id.location_dest_id.send_sicbatch \
                        and line.lot_id:
                    try:
                        connect, config = sql_connection.sql_connect(self)
                        seq = config.sequence_lot.next_by_code(config.sequence_lot.code)
                        connection = True
                        cr = connect.cursor()
                        params = (
                            seq,
                            line.product_id.default_code,
                            line.product_id.name,
                            line.lot_id.name,
                            line.picking_id.location_dest_id.id,
                            line.picking_id.location_dest_id.name
                        )
                        sp = "spAlmacen_MateriaPrima_Lotes_Actualizar"
                        call_sp1 = cr.execute("{CALL " + sp + " (?,?,?,?,?,?)}", params)

                        utils.file_log(self, params, sp)

                        rows = cr.fetchone()
                        if not rows[0]:
                            raise UserError(sys.exc_info()[0])

                        lot = self.env['stock.production.lot'].search([
                            ('id', '=', line.lot_id.id)
                        ])

                        lot.sicbatch_lot_id = str(rows[0]).strip()
                        cr.commit()
                    except:
                        UserError(_(sys.exc_info()[0]))
                        if connection:
                            cr.rollback()

                    finally:
                        if connection:
                            cr.close()
                            connect.close()
        return res

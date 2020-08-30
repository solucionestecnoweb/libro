import functools

from odoo import fields, models, api, _
from datetime import date
from odoo.exceptions import UserError

from . import sql_connection
from . import utils


class MrpWorkorder_Extension(models.Model):
    _inherit = 'mrp.workorder'

    check_start = fields.Boolean(default=False)
    check_end = fields.Boolean(default=False)
    check_sync_start = fields.Boolean(default=False)
    check_sync_end = fields.Boolean(default=False)
    sic_batch_logs = fields.One2many('sicbatch.log', 'work_order_id')

    @api.constrains('state')
    def set_check_operations(self):
        for record in self:
            config_head = record.env['config.connection'].search(
                [('company_id.id', '=', record.production_id.company_id.id),
                 ('lines_ids.routing_id.id', '=', record.production_id.routing_id.id)])
            config_line = record.env['config.connection.line'].search(
                [('routing_id', '=', record.production_id.routing_id.id),
                 ('config_head_id.id', '=', config_head.id)])
            for operation in config_line:
                if not record.check_start and not record.check_end:
                    if record.operation_id == operation.operation_start_id:
                        record.check_start = True
                    if record.operation_id == operation.operation_end_id:
                        record.check_end = True

        return

    @api.constrains('state')
    def set_check_sic_batch(self):
        for record in self:
            config_head = record.env['config.connection'].search(
                [('company_id.id', '=', record.production_id.company_id.id),
                 ('lines_ids.routing_id.id', '=', record.production_id.routing_id.id)])
            config_line = record.env['config.connection.line'].search(
                [('routing_id', '=', record.production_id.routing_id.id),
                 ('config_head_id.id', '=', config_head.id)])
            if record.state in ('ready', 'pro'):
                for operation in config_line:
                    if record.operation_id == operation.operation_start_id:
                        if not record.check_sync_start:
                            record.check_sync_start = True
        return

    def do_finish(self):
        res = super(MrpWorkorder_Extension, self).do_finish()
        for record in self:
            if record.check_sync_end:
                raise UserError(
                    _('You must end the process using the end sicbatch button'))
        return res

    def call_start_work_order(self):
        connection = False
        monitoring = ""
        for record in self:
            if not record.production_id.bom_id.code:
                raise UserError(_('Falta Código de referencia de la lista de materiales'))
            if not record.production_id.bom_id.product_tmpl_id.default_code:
                raise UserError(_('El Producto no posee código interno'))
            if not record.production_id.bom_id.product_tmpl_id.description:
                raise UserError(_('El Producto no posee Descripción'))
            try:
                monitoring = "Starting connection"
                cnxn, config = sql_connection.sql_connect(record)
                if not config.is_offline:
                    monitoring = "Send spReceta_Actualizar"
                    connection = True
                    cursor = cnxn.cursor()
                    params = (
                    record.production_id.bom_id.code, record.production_id.bom_id.product_tmpl_id.default_code,
                    record.production_id.bom_id.product_tmpl_id.name,
                    record.production_id.bom_id.product_tmpl_id.description)
                    call_sp1 = cursor.execute("{CALL spReceta_Actualizar (?,?,?,?)}", (params))
                    row = cursor.fetchall()
                    utils.send_log(self, record, row, 'IP')

                    stock_move_line = record.env['stock.move.line'].search(
                        [('production_id', '=', record.production_id.id),
                         ('lot_id.id', '>', 0)
                         ])
                    lines = 0
                    for line in stock_move_line:
                        if not line.product_id.product_tmpl_id.categ_id.send_sicbatch:
                            continue
                        lines = lines + 1
                        monitoring = line.product_id.product_tmpl_id.default_code + "_" + line.product_id.product_tmpl_id.name
                        cursor.execute("{CALL spDetalleReceta_Actualizar (?,?,?,?,?,?)}", (
                            record.production_id.bom_id.code,
                            line.product_id.product_tmpl_id.default_code,
                            line.product_id.product_tmpl_id.name,
                            line.lot_id.sicbatch_lot_id,
                            line.product_qty,
                            lines
                        ))

                    production = record.env['mrp.production'].search(
                        [('id', '=', record.production_id.id)])

                    partner_id = 0

                    if production.order_id.partner_id.parent_id:
                        partner_id = production.order_id.partner_id.parent_id
                    else:
                        partner_id = production.order_id.partner_id

                    batch = int(round(production.product_qty / production.bom_id.product_qty))

                    params = (
                        production.id,
                        production.bom_id.code,
                        partner_id.id,
                        partner_id.name,
                        production.product_qty,
                        batch,
                        production.bom_id.product_type
                    )
                    monitoring = "send spOrdenProduccion_Actualizar"
                    call_sp1 = cursor.execute("{CALL spOrdenProduccion_Actualizar  (?,?,?,?,?,?,?)}", params)
                    row = cursor.fetchall()
                    utils.send_log(self, record, row, 'IP')
                    record.button_start()
                    # record.action_continue()
                    cursor.commit()
                    record.message_post(body="Process Sicbatch Started")
                    config_line = record.env['config.connection.line'].search(
                        [('operation_start_id', '=', record.operation_id.id)])
                    work_end = record.env['mrp.workorder'].search(
                        [('operation_id', '=', config_line.operation_end_id.id),
                         ('production_id', '=', record.production_id.id)])

                    work_end.check_sync_end = True

                    record.env.cr.execute(
                        'update mrp_workorder set check_sync_start = false where id = %s and check_sync_start = %s',
                        [record.id, True])
                    return
            except:
                if connection:
                    cursor.rollback()
                    raise UserError(_('No se pudo enviar la orden a Sicbatch ' + monitoring))
            finally:
                if connection:
                    cursor.close()
                    cnxn.close()

    def call_end_work_order(self):
        connection = False
        for record in self:
            try:
                msg = 'Error en conexión'
                connect, config = sql_connection.sql_connect(record)
                if not config.is_offline:
                    connection = True
                    cr = connect.cursor()
                    call_sp1 = cr.execute("{CALL spResultOrden (?,?)}", record.production_id.id,
                                          record.production_id.bom_id.product_type)
                    qty = 0.0
                    rows = cr.fetchall()

                    record.button_start()
                    utils.send_log(self, record, rows, 'IP')

                    if len(rows) == 0:
                        raise UserError(_("No Procesado Aún"))

                    for row in rows:
                        if row == 0:
                            raise UserError(_(msg))

                        qty = row[4]
                        if not qty:
                            raise UserError(_(msg))
                        for rec in record.raw_workorder_line_ids:
                            if rec.product_id.default_code == row[2].strip():
                                record.action_next()
                                rec.qty_done = row[3]

                    record.check_sync_end = False
                    # record.action_continue()
                    # record.do_finish()
                    cr.commit()

                    record.env.cr.execute(
                        'update mrp_workorder set check_sync_end = false where id = %s and check_sync_end = %s',
                        [record.id, True])

                    close_logs = record.env['sicbatch.log'].search([
                        ('production_id', '=', record.production_id.id)])
                    for log in close_logs:
                        log.status = 'DO'
            except:
                if connection:
                    cr.rollback()
                raise UserError(_('error al procesar datos de SicBatch ' + str(msg)))

            finally:
                if connection:
                    cr.close()
                    connect.close()
        return

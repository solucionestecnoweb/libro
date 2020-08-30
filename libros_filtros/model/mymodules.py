# -*- coding: utf-8 -*-

from odoo import fields, models, api, exceptions
import logging
from odoo.exceptions import UserError


class AccountBankSatatement(models.Model):
    _inherit = "account.bank.statement.line"
    validador = fields.Boolean(value=False)


class AccountMove(models.Model):
    _inherit = 'account.move'

    _decription = "Filtra las facturas que no aparescan en los libros"

    ocultar_libros = fields.Boolean(defaul=False, value=False)


class libro_compras(models.TransientModel):
    _inherit = "account.wizard.libro.compras"

    def get_invoice(self):
        t=self.env['account.wizard.pdf.compras']
        d=t.search([])
        d.unlink()
        cursor_resumen = self.env['account.move.line.resumen'].search([
            ('fecha_fact','>=',self.date_from),
            ('fecha_fact','<=',self.date_to),
            ('state','in',('posted','cancel' )),
            ('type','in',('in_invoice','in_refund','in_receipt'))
            ])
        for det in cursor_resumen:
            if det.invoice_id.ocultar_libros!=True:
                values={
                'name':det.fecha_fact,
                'document':det.invoice_id.name,
                'partner':det.invoice_id.partner_id.id,
                'invoice_number': det.invoice_id.invoice_number,#darrell
                'tipo_doc': det.tipo_doc,
                'invoice_ctrl_number': det.invoice_id.invoice_ctrl_number,
                'sale_total': det.total_con_iva,
                'base_imponible': det.total_base,
                'iva' : det.total_valor_iva,
                'iva_retenido': det.total_ret_iva,
                'retenido': det.vat_ret_id.name,
                'retenido_date':det.vat_ret_id.voucher_delivery_date,
                'state_retantion': det.vat_ret_id.state,
                'state': det.invoice_id.state,
                'currency_id':det.invoice_id.currency_id.id,
                'ref':det.invoice_id.ref,
                'total_exento':det.total_exento,
                'alicuota_reducida':det.alicuota_reducida,
                'alicuota_general':det.alicuota_general,
                'alicuota_adicional':det.alicuota_adicional,
                'base_adicional':det.base_adicional,
                'base_reducida':det.base_reducida,
                'base_general':det.base_general,
                'retenido_reducida':det.retenido_reducida,
                'retenido_adicional':det.retenido_adicional,
                'retenido_general':det.retenido_general,
                'vat_ret_id':det.vat_ret_id.id,
                'invoice_id':det.invoice_id.id,
                'tax_id':det.tax_id.id,
                }
                pdf_id = t.create(values)
        #   temp = self.env['account.wizard.pdf.ventas'].search([])
        self.line = self.env['account.wizard.pdf.compras'].search([])

class libro_ventas(models.TransientModel):
    _inherit = "account.wizard.libro.ventas"


    def get_invoice(self,accion):
        t=self.env['account.wizard.pdf.ventas']
        d=t.search([])
        #d.unlink()
        if accion=="factura":
            cursor_resumen = self.env['account.move.line.resumen'].search([
                ('fecha_fact','>=',self.date_from),
                ('fecha_fact','<=',self.date_to),
                ('state','in',('posted','cancel' )),
                ('type','in',('out_invoice','out_refund','out_receipt'))
                ])
        if accion=="voucher":
            cursor_resumen = self.env['account.move.line.resumen'].search([
                ('fecha_comprobante','>=',self.date_from),
                ('fecha_comprobante','<=',self.date_to),
                ('fecha_fact','<=',self.date_from),
                #('fecha_fact','>=',self.date_to),
                ('state_voucher_iva','=','posted'),
                ('type','in',('out_invoice','out_refund','out_receipt'))
                ])
        for det in cursor_resumen:
            if det.invoice_id.ocultar_libros!=True:
                alicuota_reducida=0
                alicuota_general=0
                alicuota_adicional=0
                base_adicional=0
                base_reducida=0
                base_general=0
                total_con_iva=0
                total_base=0
                total_exento=0
                if accion=="factura":
                    alicuota_reducida=det.alicuota_reducida
                    alicuota_general=det.alicuota_general
                    alicuota_adicional=det.alicuota_adicional
                    base_adicional=det.base_adicional
                    base_reducida=det.base_reducida
                    base_general=det.base_general
                    total_con_iva=det.total_con_iva
                    total_base=det.total_base
                    total_exento=det.total_exento
                values={
                'name':det.fecha_fact,
                'document':det.invoice_id.name,
                'partner':det.invoice_id.partner_id.id,
                'invoice_number': det.invoice_id.invoice_number,#darrell
                'tipo_doc': det.tipo_doc,
                'invoice_ctrl_number': det.invoice_id.invoice_ctrl_number,
                'sale_total': total_con_iva,
                'base_imponible': total_base,
                'iva' : det.total_valor_iva,
                'iva_retenido': det.total_ret_iva,
                'retenido': det.vat_ret_id.name,
                'retenido_date':det.vat_ret_id.voucher_delivery_date,
                'state_retantion': det.vat_ret_id.state,
                'state': det.invoice_id.state,
                'currency_id':det.invoice_id.currency_id.id,
                'ref':det.invoice_id.ref,
                'total_exento': total_exento,
                'alicuota_reducida':alicuota_reducida,
                'alicuota_general':alicuota_general,
                'alicuota_adicional':alicuota_adicional,
                'base_adicional':base_adicional,
                'base_reducida':base_reducida,
                'base_general':base_general,
                'retenido_reducida':det.retenido_reducida,
                'retenido_adicional':det.retenido_adicional,
                'retenido_general':det.retenido_general,
                'vat_ret_id':det.vat_ret_id.id,
                'invoice_id':det.invoice_id.id,
                }
                pdf_id = t.create(values)
        #   temp = self.env['account.wizard.pdf.ventas'].search([])
        self.line = self.env['account.wizard.pdf.ventas'].search([])
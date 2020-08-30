from odoo import fields, models, api
from . import utils


class Assets(models.Model):
    _inherit = 'account.asset'

    operation_currency = fields.Many2one('res.currency')
    rate = fields.Float()

    @api.onchange('operation_currency')
    def get_default_rate(self):
        for record in self:
            if self.operation_currency:
                self.rate = utils.get_rate(record)

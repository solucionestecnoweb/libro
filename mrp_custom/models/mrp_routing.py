from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


class MrpRouting(models.Model):
    _inherit = 'mrp.routing'

    capacity_batch = fields.Float()

    @api.constrains('capacity_batch')
    def validate_zero(self):
        for record in self:
            if record.capacity_batch == 0:
                raise ValidationError(_(
                    'The quantity cannot be equal to zero'))

# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, exceptions, fields, models


class StockLot(models.Model):
    _inherit = "stock.lot"

    manufacturing_routing_revision_id = fields.Many2one(
        "manufacturing.routing.revision",
        domain="[('allowed_product_ids', 'in', product_id)]",
    )

    @api.constrains("product_id")
    def _check_existing_manufacturing_routing_revision(self):
        for lot in self:
            if (
                lot.product_id.manufacturing_routing_ids
            ) and not lot.manufacturing_routing_revision_id:
                raise exceptions.UserError(
                    self.env._(
                        "The manufacturing routing revision is mandatory on lot "
                        "%(lot)s for product %(product)s",
                        lot=lot.name,
                        product=lot.product_id.default_code,
                    )
                )

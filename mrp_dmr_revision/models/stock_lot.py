# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, exceptions, fields, models


class StockLot(models.Model):
    _inherit = "stock.lot"

    dmr_revision_id = fields.Many2one(
        "dmr.revision",
        domain="[('allowed_product_ids', 'in', product_id)]",
    )

    @api.constrains("product_id")
    def _check_existing_dmr_revision(self):
        for lot in self:
            if (lot.product_id.dmr_id) and not lot.dmr_revision_id:
                raise exceptions.UserError(
                    self.env._(
                        "The DMR revision is mandatory on lot "
                        "%(lot)s for product %(product)s",
                        lot=lot.name,
                        product=lot.product_id.default_code,
                    )
                )

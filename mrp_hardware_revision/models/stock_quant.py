# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, exceptions, fields, models
from odoo.osv import expression


class StockQuant(models.Model):
    _inherit = "stock.quant"

    hardware_revision_id = fields.Many2one(
        "product.hardware.revision",
        related="lot_id.hardware_revision_id",
        store=True,
        index="btree",
    )

    def _get_gather_domain(
        self,
        product_id,
        location_id,
        lot_id=None,
        package_id=None,
        owner_id=None,
        strict=False,
    ):
        domain = super()._get_gather_domain(
            product_id,
            location_id,
            lot_id=lot_id,
            package_id=package_id,
            owner_id=owner_id,
            strict=strict,
        )
        if self.env.context.get("hw_revision"):
            hw_revision = self.env.context.get("hw_revision")
            domain = expression.AND(
                [[("hardware_revision_id", "=", hw_revision.id)], domain]
            )
        return domain

    @api.constrains("location_id", "lot_id")
    def _check_no_prototype_stock(self):
        for quant in self:
            stock_loc = quant.warehouse_id.lot_stock_id
            if (
                stock_loc
                and quant.lot_id.prototype
                and quant.location_id in stock_loc.child_internal_location_ids
            ):
                raise exceptions.UserError(
                    self.env._(
                        "The lot %(lot)s for product %(ref)s is a prototype and you "
                        "can't move it to the sellable stock",
                        lot=quant.lot_id.name,
                        ref=quant.product_id.default_code,
                    )
                )

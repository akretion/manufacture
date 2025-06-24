# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import exceptions, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def button_approve(self, force=False):
        missing_routing_version_products = self.order_line.filtered(
            lambda line: not line.manufacturing_routing_revision_id
            and line.product_id.manufacturing_routing_ids
        ).product_id
        if missing_routing_version_products:
            raise exceptions.UserError(
                self.env._(
                    "The manufacturing routing revision is missing for products "
                    "%(codes)s",
                    codes=missing_routing_version_products.mapped("default_code"),
                )
            )
        return super().button_approve(force=force)

# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import exceptions, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _get_eco_warning(self):
        message = super()._get_eco_warning()
        product_ids = self.order_line.product_id.ids
        dmrs = self.env["dmr"].search(
            [
                "|",
                ("product_ids", "in", product_ids),
                ("linked_product_ids", "in", product_ids),
            ]
        )
        ongoing_ecos = self.env["engineering.change.order"].search(
            [("state", "not in", ("4-done",)), ("dmr_ids", "in", dmrs.ids)]
        )
        if ongoing_ecos:
            if message:
                message += "\n"
            message += self.env._(
                "The DMRs %(dmr_names)s are under change. The change orders are "
                "the following : %(eco_names)s",
                dmr_names=dmrs.mapped("name"),
                eco_names=ongoing_ecos.mapped("name"),
            )
        return message

    def button_approve(self, force=False):
        missing_dmr_version_products = self.order_line.filtered(
            lambda line: not line.dmr_revision_id and line.product_id.dmr_id
        ).product_id
        if missing_dmr_version_products:
            raise exceptions.UserError(
                self.env._(
                    "The DMR revision is missing for products " "%(codes)s",
                    codes=missing_dmr_version_products.mapped("default_code"),
                )
            )
        return super().button_approve(force=force)

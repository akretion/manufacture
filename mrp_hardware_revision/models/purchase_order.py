# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    ongoing_eco_message = fields.Text(compute="_compute_ongoing_eco_message")

    @api.depends("order_line.product_id")
    def _compute_ongoing_eco_message(self):
        for rec in self:
            product_ids = self.order_line.product_id.ids
            plans = self.env["hardware.plan"].search(
                [
                    "|",
                    ("product_ids", "in", product_ids),
                    ("additional_product_ids", "in", product_ids),
                ]
            )
            ongoing_ecos = self.env["engineering.change.order"].search(
                [("state", "not in", ("4-done",)), ("plan_ids", "in", plans.ids)]
            )
            message = ""
            if ongoing_ecos:
                message = self.env._(
                    "The plans %(plan_names)s are under change. The change orders are "
                    "the following : %(eco_names)s",
                    plan_names=plans.mapped("name"),
                    eco_names=ongoing_ecos.mapped("name"),
                )
            rec.ongoing_eco_message = message

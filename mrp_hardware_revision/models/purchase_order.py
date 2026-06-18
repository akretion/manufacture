# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, exceptions, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    ongoing_eco_message = fields.Text(compute="_compute_ongoing_eco_message")

    def _get_eco_warning(self):
        self.ensure_one()
        product_ids = self.order_line.product_id.ids
        plans = self.env["hardware.plan"].search(
            [
                "|",
                ("product_ids", "in", product_ids),
                ("linked_product_ids", "in", product_ids),
            ]
        )
        ongoing_ecos = self.env["engineering.change.order"].search(
            [("state", "not in", ("4-done",)), ("plan_ids", "in", plans.ids)]
        )
        plans_under_change = ongoing_ecos.plan_ids
        message = ""
        if ongoing_ecos:
            eco_lines = [
                f"{eco.name}: {eco.description}" if eco.description else eco.name
                for eco in ongoing_ecos
            ]
            message = self.env._(
                "The plans %(plan_names)s are under change. The change orders are "
                "the following : \n- %(eco_names)s",
                plan_names=", ".join(plans_under_change.mapped("name")),
                eco_names="\n- ".join(eco_lines),
            )
        return message

    @api.depends("order_line.product_id")
    def _compute_ongoing_eco_message(self):
        for rec in self:
            message = rec._get_eco_warning()
            rec.ongoing_eco_message = message

    def button_approve(self, force=False):
        missing_hr_products = self.order_line.filtered(
            lambda line: not line.hardware_revision_id and line.product_id.plan_id
        ).product_id
        if missing_hr_products:
            raise exceptions.UserError(
                self.env._(
                    "The hardware revision is missing for products %(codes)s",
                    codes=missing_hr_products.mapped("default_code"),
                )
            )
        return super().button_approve(force=force)

# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    eco_id = fields.Many2one("engineering.change.order")
    previous_bom_id = fields.Many2one("mrp.bom")

    def _trigger_plan_recomputation_from_bom(self):
        """When a BoM is changed, find plans of its components and trigger
        recomputation."""
        plans_to_recompute = self.bom_line_ids.product_id.plan_id
        if plans_to_recompute:
            plans_to_recompute.recompute_linked_products()

    def write(self, vals):
        """
        Trigger recomputation if fields that affect the BoM structure are changed,
        such as 'active' or the BoM's product itself.
        """
        plans_before = self.env["hardware.plan"]
        if "active" in vals or "product_tmpl_id" in vals or "product_id" in vals:
            plans_before = self.bom_line_ids.product_id.plan_id

        res = super().write(vals)

        if "active" in vals or "product_tmpl_id" in vals or "product_id" in vals:
            plans_after = self.bom_line_ids.product_id.plan_id
            plans_to_recompute = plans_before | plans_after
            if plans_to_recompute:
                plans_to_recompute.recompute_linked_products()

        return res

    def unlink(self):
        """Trigger recomputation before unlinking the BoM."""
        self._trigger_plan_recomputation_from_bom()
        return super().unlink()

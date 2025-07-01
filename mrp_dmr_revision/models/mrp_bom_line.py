# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    def _trigger_dmr_recomputation(self):
        """Find plans related to the components and trigger recomputation."""
        dmrs_to_recompute = self.product_id.dmr_id
        if dmrs_to_recompute:
            dmrs_to_recompute.recompute_linked_products()

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._trigger_plan_recomputation()
        return lines

    def write(self, vals):
        old_plans = self.env["hardware.plan"]
        if "product_id" in vals:
            old_plans = self.product_id.plan_id

        res = super().write(vals)

        new_plans = self.env["hardware.plan"]
        if "product_id" in vals:
            new_plans = self.product_id.plan_id

        plans_to_recompute = old_plans | new_plans
        if plans_to_recompute:
            plans_to_recompute.recompute_linked_products()

        return res

    def unlink(self):
        plans_to_recompute = self.product_id.plan_id
        res = super().unlink()
        if plans_to_recompute:
            plans_to_recompute.recompute_linked_products()
        return res

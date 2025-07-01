# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    def _trigger_dmr_recomputation_from_bom(self):
        """When a BoM is changed, find dmrs of its components and trigger
        recomputation."""
        dmrs_to_recompute = self.bom_line_ids.product_id.dmr_id
        if dmrs_to_recompute:
            dmrs_to_recompute.recompute_linked_products()

    def write(self, vals):
        """
        Trigger recomputation if fields that affect the BoM structure are changed,
        such as 'active' or the BoM's product itself.
        """
        dmrs_before = self.env["dmr"]
        if "active" in vals or "product_tmpl_id" in vals or "product_id" in vals:
            dmrs_before = self.bom_line_ids.product_id.dmr_id

        res = super().write(vals)

        if "active" in vals or "product_tmpl_id" in vals or "product_id" in vals:
            dmrs_after = self.bom_line_ids.product_id.dmr_id
            dmrs_to_recompute = dmrs_before | dmrs_after
            if dmrs_to_recompute:
                dmrs_to_recompute.recompute_linked_products()

        return res

    def unlink(self):
        """Trigger recomputation before unlinking the BoM."""
        self._trigger_dmr_recomputation_from_bom()
        return super().unlink()

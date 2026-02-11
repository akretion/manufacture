# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models
from odoo.tools import float_compare


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def action_confirm(self):
        res = super().action_confirm()
        for production in self.filtered(lambda mo: mo.state == "confirmed"):
            bom = production.bom_id
            batch_qty = bom.batch_quantity
            if (
                not bom
                or not batch_qty
                or batch_qty == production.product_qty
                or bom.product_uom_id != production.product_uom_id
            ):
                continue
            split_quantities = {production: []}
            remaining_qty = production.product_qty
            while (
                float_compare(
                    remaining_qty,
                    0,
                    precision_rounding=production.product_uom_id.rounding,
                )
                > 0
            ):
                current_batch = min(batch_qty, remaining_qty)
                remaining_qty -= current_batch
                split_quantities[production].append(current_batch)
            production._split_productions(amounts=split_quantities)
        return res

    def _get_backorder_mo_vals(self):
        vals = super()._get_backorder_mo_vals()
        # propagate lot if any and not started yet.
        if self.state == "confirmed":
            vals["lot_producing_id"] = self.lot_producing_id.id
        return vals

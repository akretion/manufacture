# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, models
from odoo.tools import float_compare


class StockRule(models.Model):
    _inherit = "stock.rule"

    @api.model
    def _run_manufacture(self, procurements):
        new_procurements = []
        for procurement, rule in procurements:
            bom = rule._get_matching_bom(
                procurement.product_id, procurement.company_id, procurement.values
            )
            batch_qty = bom.batch_quantity
            if (
                not batch_qty
                or batch_qty == procurement.product_qty
                or not procurement.product_qty
            ):
                new_procurements.append((procurement, rule))
            else:
                uom = procurement.product_uom
                remaining_qty = procurement.product_qty
                while (
                    float_compare(remaining_qty, 0, precision_rounding=uom.rounding) > 0
                ):
                    current_batch = min(batch_qty, remaining_qty)
                    remaining_qty -= current_batch
                    new_procurements.append(
                        (procurement._replace(product_qty=current_batch), rule)
                    )
        return super()._run_manufacture(new_procurements)

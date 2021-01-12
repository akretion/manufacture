# Copyright 2019 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _prepare_mo_vals(
        self,
        product_id,
        product_qty,
        product_uom,
        location_id,
        name,
        origin,
        values,
        bom,
    ):
        res = super()._prepare_mo_vals(
            product_id, product_qty, product_uom, location_id, name, origin, values, bom
        )
        if self.env.context.get("parent_mrp_production_id"):
            parent_id_nb = self.env.context["parent_mrp_production_id"]
            root_id_nb = self.env.context["root_mrp_production_id"]

            parent_id = self.env["mrp.production"].browse([parent_id_nb])
            parent_level = parent_id.hierarchy_level

            res.update(
                {
                    "parent_id": parent_id_nb,
                    "root_id": root_id_nb,
                    "hierarchy_level": parent_level + 1,
                }
            )
        return res

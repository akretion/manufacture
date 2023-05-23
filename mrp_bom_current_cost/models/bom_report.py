import logging

from odoo import api, models

logger = logging.getLogger(__name__)


class ReportBomStructure(models.AbstractModel):
    _inherit = "report.mrp.report_bom_structure"

    def _get_bom_lines(self, bom, bom_quantity, product, line_id, level):
        components, total = super()._get_bom_lines(
            bom, bom_quantity, product, line_id, level
        )
        products = self.env["product.product"].browse(
            [component.get("prod_id", 0) for component in components]
        )
        for compo in components:
            compo["current_cost"] = (
                products.filtered(lambda s: s.id == compo["prod_id"]).current_cost
                * compo["prod_qty"]
            )
        return components, total

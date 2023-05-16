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


# {'prod_id': 52, 'prod_name': '[MP2] MP2 DEMO', 'code': '', 'prod_qty': 2.0, 'prod_uom': 'Unit(s)',
#     'prod_cost': 0.0, 'parent_id': 10, 'line_id': 22, 'level': 1, 'total': 0.0, 'child_bom': False, 'phantom_bom': False, 'attachments': mrp.document()},
# {'prod_id': 54, 'prod_name': '[MP3] MP3 DEMO', 'code': '', 'prod_qty': 1.0, 'prod_uom': 'Unit(s)',
#     'prod_cost': 41.0, 'parent_id': 10, 'line_id': 24, 'level': 1, 'total': 41.0, 'child_bom': False, 'phantom_bom': False, 'attachments': mrp.document()}]

# - exception sur produit

# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _prepare_subcontract_mo_vals(self, move, bom):
        vals = super()._prepare_subcontract_mo_vals(move, bom)
        if move.purchase_line_id.hardware_revision_id:
            vals["hardware_revision_id"] = move.purchase_line_id.hardware_revision_id.id
        return vals

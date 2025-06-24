# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _prepare_new_lot_vals(self):
        vals = super()._prepare_new_lot_vals()
        routing_revision = self.move_id._get_manufacturing_routing_revision()
        vals["manufacturing_routing_revision_id"] = routing_revision.id
        return vals

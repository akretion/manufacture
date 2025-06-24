# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_manufacturing_routing_revision(self):
        self.ensure_one()
        return self.purchase_line_id.manufacturing_routing_revision_id

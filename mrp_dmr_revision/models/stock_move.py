# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_dmr_revision(self):
        self.ensure_one()
        return self.purchase_line_id.dmr_revision_id

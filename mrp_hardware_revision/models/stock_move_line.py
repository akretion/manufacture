# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _prepare_new_lot_vals(self):
        vals = super()._prepare_new_lot_vals()
        hardware_revision = self.move_id._get_hardware_revision()
        vals["hardware_revison_id"] = hardware_revision.id
        return vals

# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _get_custom_move_fields(self):
        fields = super()._get_custom_move_fields()
        fields += ["restrict_hardware_revision_id"]
        return fields

    def _push_prepare_move_copy_values(self, move_to_copy, new_date):
        values = super()._push_prepare_move_copy_values(move_to_copy, new_date)
        values["restrict_hardware_revision_id"] = (
            move_to_copy.restrict_hardware_revision_id.id
        )
        return values

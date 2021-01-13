# Copyright (C) 2020 - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, api, _, fields


class StockMove(models.Model):
    _inherit = "stock.picking"

    css_class = fields.Char(
        string="CSS class",
        compute="_compute_css_class",
        help="Bootstrap CSS class used in hierarchy report to inform about the "
        "'stock.move' progress",
    )

    @api.depends("state")
    def _compute_css_class(self):
        for pick in self:
            if pick.state in ("draft", "waiting"):
                pick.css_class = "text-danger"
            elif (
                pick.state in ("confirmed", "assigned") and pick.show_check_availability
            ):
                pick.css_class = "text-warning"
            # show_check_availability is False only where there is no more move to
            # reserve. Only then the full picking is ready to be validated.
            elif pick.state == "assigned" and not pick.show_check_availability:
                pick.css_class = "text-success"
            elif pick.state in ("done", "cancel"):
                pick.css_class = "text-muted"

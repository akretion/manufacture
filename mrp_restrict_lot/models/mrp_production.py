# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    lot_producing_ids = fields.Many2many(
        compute="_compute_lot_producing_ids",
        inverse="_inverse_lot_producing_ids",
        store=True,
        readonly=False,
    )

    @api.depends("move_finished_ids.restrict_lot_id")
    def _compute_lot_producing_ids(self):
        for order in self:
            restricted_lot = order.move_finished_ids.filtered(
                lambda m, order=order: m.product_id == order.product_id
            ).restrict_lot_id
            if restricted_lot:
                order.lot_producing_ids = restricted_lot

    def _inverse_lot_producing_ids(self):
        for order in self:
            move_finished = order.move_finished_ids.filtered(
                lambda m, order=order: m.product_id == order.product_id
            )
            if move_finished:
                new_lot = order.lot_producing_ids[:1]
                move_finished.restrict_lot_id = new_lot
                move_finished.move_line_ids.filtered(
                    lambda ml: ml.state not in ("done", "cancel")
                ).lot_id = new_lot

# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    availability_zone_id = fields.Many2one(
        "stock.location",
        help="Filled if raw material availability is checked on another zone than the "
        "raw material consumption location",
    )
    had_shortage = fields.Boolean(
        help="This box should be checked if, at any point, the raw material "
        "of this Manufacture Order has been out of stock."
    )
    available_date = fields.Date(
        help="Date from when the manufacture order was ready to produce after"
        " a shortage"
    )

    def _get_availability_zone(self):
        self.ensure_one()
        # By default the parent location of consumption location is checked
        return self.location_src_id.location_id

    def action_confirm(self):
        res = super().action_confirm()
        for mo in self:
            availability_zone = mo._get_availability_zone()
            mo.write({"availability_zone_id": availability_zone.id})
        self.mapped("move_raw_ids").with_delay().check_mrp_raw_material_availability()
        return res

    def force_assign(self):
        raw_moves = self.mapped("move_raw_ids").filtered(
            lambda m: m.state == "confirmed"
        )
        raw_moves.write("assigned")

    # replace class reservation odoo way by our mrp way
    def action_assign(self):
        self.mapped("move_raw_ids").check_mrp_raw_material_availability()

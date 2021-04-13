# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class MrpRoutingWorkcenter(models.Model):
    _inherit = "mrp.routing.workcenter"

    dependency_ids = fields.Many2many(
        "mrp.routing.workcenter",
        "rel_dependency_routing_worcenter",
        "routing_id",
        "routing_dependency_id",
        "Depend On",
        copy=False,
    )
    dependency_for_ids = fields.Many2many(
        "mrp.routing.workcenter",
        "rel_dependency_routing_worcenter",
        "routing_dependency_id",
        "routing_id",
        "Dependency For",
        copy=False,
    )

    def write(self, vals):
        res = super().write(vals)
        if "dependency_ids" in vals:
            wos = self.env["mrp.workorder"].search(
                [
                    ("operation_id", "in", self.ids),
                    ("state", "not in", ("cancel", "done")),
                ]
            )
            wos.check_waiting_state()
        return res

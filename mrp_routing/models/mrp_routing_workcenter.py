# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MrpRoutingWorkcenter(models.Model):
    _inherit = "mrp.routing.workcenter"

    routing_id = fields.Many2one(
        "mrp.routing",
        "Parent Routing",
        index=True,
        ondelete="cascade",
        help="The routing contains all the Work Centers used and for how long. "
        "This will create work orders afterwards "
        "which alters the execution of the manufacturing order.",
    )

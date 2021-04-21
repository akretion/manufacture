# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    @api.depends("routing_id.operation_ids")
    def _compute_operation_ids(self):
        for bom in self:
            if bom.routing_id:
                operations = bom.routing_id.operation_ids
            else:
                operations = self.env["mrp.routing.workcenter"].search(
                    [("bom_id", "=", bom.id)]
                )
            bom.operation_ids = operations

    operation_ids = fields.One2many(compute="_compute_operation_ids", store=False)
    routing_id = fields.Many2one("mrp.routing", string="Routing")

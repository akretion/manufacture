# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    manufacturing_routing_revision_id = fields.Many2one(
        "manufacturing.routing.revision",
        compute="_compute__manufacturing_routing_revision_id",
        domain="[('allowed_product_ids', 'in', product_id), ('prototype', '=', prototype), ('is_current_revision', '!=', prototype)]",  # noqa E501
        store=True,
        readonly=False,
    )

    @api.depends("product_id", "prototype")
    def _compute_manufacturing_routing_revision_id(self):
        for pol in self:
            pol.manufacturing_routing_revision_id = (
                pol.product_id._get_default_manufacturing_routing_revision(
                    prototype=pol.prototype
                )
            )

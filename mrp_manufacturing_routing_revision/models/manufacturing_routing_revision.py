# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.fields import first


class ManufacturingRoutingRevision(models.Model):
    _name = "manufacturing.routing.revision"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Manufacturing Routing Revision"
    _order = "start_date desc, name desc"
    _rec_names_search = ["name", "manufacturing_routing_id.name"]

    name = fields.Char(required=True)
    manufacturing_routing_id = fields.Many2one("manufacturing.routing", required=True)
    #    product_tmpl_id = fields.Many2one(
    #        "product.template", related="product_id.product_tmpl_id")
    allowed_product_ids = fields.Many2many(
        "product.product", compute="_compute_allowed_product_ids", store=True
    )
    prototype = fields.Boolean()
    generated_by_eco_id = fields.Many2one("engineering.change.order")
    start_date = fields.Date(copy=False)
    is_current_revision = fields.Boolean(
        compute="_compute_is_current_revision", store=True
    )

    @api.depends("manufacturing_routing_id", "name")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.manufacturing_routing_id.name} - {rec.name}"

    @api.depends("manufacturing_routing_id.product_ids")
    def _compute_allowed_product_ids(self):
        for rec in self:
            rec.allowed_product_ids = rec.manufacturing_routing_id.product_ids

    @api.depends("manufacturing_routing_id.revision_ids.start_date")
    def _compute_is_current_revision(self):
        for rec in self:
            revisions = rec.manufacturing_routing_id.revision_ids.filtered(
                lambda rec: rec.start_date
            )
            if rec.start_date and rec == first(revisions):
                rec.is_current_revision = True
            else:
                rec.is_current_revision = False

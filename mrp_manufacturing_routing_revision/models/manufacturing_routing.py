# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, exceptions, fields, models


class ManufacturingRouting(models.Model):
    _name = "manufacturing.routing"
    _description = "Manufacturing Routing"

    name = fields.Char(required=True)
    product_ids = fields.Many2many(
        "product.product",
        relation="manufacturing_routing_product_rel",
        column1="manufacturing_routing_id",
        column2="product_id",
        help="Products concerned by manufacturing routing",
    )
    current_revision_id = fields.Many2one(
        "manufacturing.order.revision", compute="_compute_current_revision_id"
    )
    prototype_revision_id = fields.Many2one(
        "manufacturing.order.revision", compute="_compute_prototype_revision_id"
    )
    revision_ids = fields.One2many(
        "manufacturing.routing.revision", "manufacturing_routing_id"
    )

    @api.constrains("product_ids")
    def _check_no_product_multiple_routing(self):
        for rec in self:
            for product in rec.product_ids:
                if len(product.manufacturing_routing_ids) > 1:
                    raise exceptions.UserError(
                        self.env._(
                            "Problem of configuration with %(product_code)s, it is "
                            "linked to multiple manufacturing routing and this is not "
                            "possible",
                            product_code=product.default_code,
                        )
                    )

    @api.depends("revision_ids.is_current_revision")
    def _compute_current_revision_id(self):
        for rec in self:
            rec.current_revision_id = rec.revision_ids.filtered(
                lambda rev: rev.is_current_revision
            )

    @api.depends("revision_ids.prototype")
    def _compute_prototype_revision_id(self):
        for rec in self:
            rec.prototype_revision_id = rec.revision_ids.filtered(
                lambda rev: rev.prototype
            )

    _sql_constraints = [
        ("unique_name", "UNIQUE(name)", "The name must be unique"),
    ]

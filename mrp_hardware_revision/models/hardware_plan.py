# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HardwarePlan(models.Model):
    _name = "hardware.plan"
    _description = "Hardware Plan"

    name = fields.Char(required=True)
    product_ids = fields.Many2many(
        "product.product",
        help="Products directly concerned by the plan, usually semi-finished products.",
    )
    additional_product_ids = fields.Many2many(
        "product.product",
        relation="plan_additional_product_rel",
        column1="plan_id",
        column2="product_id",
        help="Product sharing the plan because they are derivec from these semi-finished product.",
    )
    current_revision_id = fields.Many2one(
        "product.hardware.revision", compute="_compute_current_revision_id"
    )
    prototype_revision_id = fields.Many2one(
        "product.hardware.revision", compute="_compute_prototype_revision_id"
    )
    revision_ids = fields.One2many("product.hardware.revision", "plan_id")

    @api.depends("revision_ids.is_current_revision")
    def _compute_current_revision_id(self):
        for plan in self:
            plan.current_revision_id = plan.revision_ids.filtered(
                lambda rev: rev.is_current_revision
            )

    @api.depends("revision_ids.prototype")
    def _compute_prototype_revision_id(self):
        for plan in self:
            plan.prototype_revision_id = plan.revision_ids.filtered(
                lambda rev: rev.prototype
            )

    _sql_constraints = [
        ("unique_name", "UNIQUE(name)", "The name must be unique"),
    ]

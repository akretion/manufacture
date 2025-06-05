# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, exceptions, fields, models


class HardwarePlan(models.Model):
    _name = "hardware.plan"
    _description = "Hardware Plan"

    name = fields.Char(required=True)
    product_ids = fields.Many2many(
        "product.product",
        relation="plan_product_rel",
        column1="plan_id",
        column2="product_id",
        help="Products directly concerned by the plan, usually semi-finished products.",
    )
    linked_product_ids = fields.Many2many(
        "product.product",
        relation="plan_link_product_rel",
        column1="plan_id",
        column2="product_id",
        help="Product sharing the plan because they are derived from these "
        "semi-finished product.",
    )
    current_revision_id = fields.Many2one(
        "product.hardware.revision", compute="_compute_current_revision_id"
    )
    prototype_revision_id = fields.Many2one(
        "product.hardware.revision", compute="_compute_prototype_revision_id"
    )
    revision_ids = fields.One2many("product.hardware.revision", "plan_id")

    # seems hard to make it compute because of recursivity
    def update_linked_products(self):
        for plan in self:
            linked_products = self.env["product.product"]
            products = plan.product_ids
            while products:
                derivated_products = products._get_derivative_product()
                if derivated_products:
                    linked_products |= derivated_products
                products = derivated_products
            plan.write({"linked_product_ids": [(6, 0, linked_products.ids)]})

    @api.constrains("product_ids")
    def _check_no_product_multiple_plan(self):
        for plan in self:
            for product in plan.product_ids:
                if len(product.plan_ids) > 1:
                    raise exceptions.UserError(
                        self.env._(
                            "Problem of configuration with %(product_code)s, it is "
                            "linked to multiple plan and this is not possible",
                            product_code=product.default_code,
                        )
                    )

    @api.constrains("linked_product_ids")
    def _check_no_link_product_multiple_plan(self):
        for plan in self:
            for product in plan.linked_product_ids:
                if len(product.linked_plan_ids) > 1:
                    raise exceptions.UserError(
                        self.env._(
                            "Problem of configuration with %(product_code)s, it is "
                            "linked to multiple plan and this is not possible",
                            product_code=product.default_code,
                        )
                    )

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

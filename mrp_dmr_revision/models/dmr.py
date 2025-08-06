# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, exceptions, fields, models


class DMR(models.Model):
    _name = "dmr"
    _description = "Device Master Record"

    name = fields.Char(required=True)
    product_ids = fields.Many2many(
        "product.product",
        relation="dmr_product_rel",
        column1="dmr_id",
        column2="product_id",
        help="Products concerned by DMR",
    )
    linked_product_ids = fields.Many2many(
        "product.product",
        relation="dmr_link_product_rel",
        column1="dmr_id",
        column2="product_id",
        help="Product sharing the DMR because they are derived from these "
        "semi-finished product.",
        compute="_compute_linked_product_ids",
        store=True,
    )
    current_revision_id = fields.Many2one(
        "dmr.revision", compute="_compute_current_revision_id"
    )
    prototype_revision_id = fields.Many2one(
        "dmr.revision", compute="_compute_prototype_revision_id"
    )
    revision_ids = fields.One2many("dmr.revision", "dmr_id")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

    @api.depends("product_ids")
    def _compute_linked_product_ids(self):
        """
        Compute the linked products by recursively exploring the BoM structure.
        This method is triggered automatically when `product_ids` changes, and
        manually from overrides on `mrp.bom` and `mrp.bom.line`.
        """
        for plan in self:
            linked_products = self.env["product.product"]
            products_to_process = plan.product_ids
            # Keep track of all products processed (direct, linked, and intermediate)
            # to avoid infinite loops in case of recursive BoMs.
            processed_products = products_to_process
            while products_to_process:
                derivated_products = products_to_process._get_derivative_dmr_product()
                if not derivated_products:
                    break
                # We only continue with derivatives that have not been processed yet.
                new_derivatives = derivated_products - processed_products
                if not new_derivatives:
                    break
                linked_products |= new_derivatives
                processed_products |= new_derivatives
                products_to_process = new_derivatives
            plan.linked_product_ids = [(6, 0, linked_products.ids)]

    def recompute_linked_products(self):
        """
        Mark `linked_product_ids` to be recomputed.
        This method is called from `mrp.bom` and `mrp.bom.line` overrides
        when the BoM structure changes.
        """
        if not self:
            return
        self.env.add_to_compute(self._fields["linked_product_ids"], self)

    @api.constrains("product_ids")
    def _check_no_product_multiple_dmr(self):
        for rec in self:
            for product in rec.product_ids:
                if len(product.dmr_ids) > 1:
                    raise exceptions.UserError(
                        self.env._(
                            "Problem of configuration with %(product_code)s, it is "
                            "linked to multiple DMR and this is not "
                            "possible",
                            product_code=product.default_code,
                        )
                    )

    @api.constrains("linked_product_ids")
    def _check_no_link_product_multiple_routing(self):
        for rec in self:
            for product in rec.linked_product_ids:
                if len(product.linked_dmr_ids) > 1:
                    raise exceptions.UserError(
                        self.env._(
                            "Problem of configuration with %(product_code)s, it is "
                            "linked to multiple DMR and this is not possible",
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
        ("unique_name", "UNIQUE(name, company_id)", "The name must be unique"),
    ]

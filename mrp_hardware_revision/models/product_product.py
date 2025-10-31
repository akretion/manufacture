# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _get_default_hardware_revision(self, prototype=False):
        # expect recordset of 1 record or empty
        plan = self.env["hardware.plan"].search(
            [
                "|",
                ("product_ids", "in", self.ids),
                ("linked_product_ids", "in", self.ids),
            ]
        )
        if prototype:
            return plan.prototype_revision_id
        else:
            return plan.current_revision_id

    # for now technical field
    plan_ids = fields.Many2many(
        "hardware.plan",
        relation="plan_product_rel",
        column1="product_id",
        column2="plan_id",
        string="direct plan",
        help="Direct plan of this product",
    )
    linked_plan_ids = fields.Many2many(
        "hardware.plan",
        relation="plan_link_product_rel",
        column1="product_id",
        column2="plan_id",
        help="Herited plan (from component)",
    )
    plan_id = fields.Many2one("hardware.plan", compute="_compute_plan_id", store=True)
    # only to solve bug in eco form view due to onchange with m2o in one2many view...
    # It is a related to plan_id because computed in _compute_plan_id
    # we do not set it to related because then it won't work in the form view
    # of ecos. On ecos, product_ids make a read on Newid recordset somehow and it
    # does not get the computed fields...
    plan_id_name = fields.Char()

    @api.depends("plan_ids", "linked_plan_ids")
    def _compute_plan_id(self):
        for product in self:
            plan = product.plan_ids or product.linked_plan_ids
            product.plan_id = plan and plan[0].id or False
            product.plan_id_name = plan.name

    def _get_derivative_plan_product(self):
        derivated_products = self.env["product.product"]
        for product in self:
            # used_in_bom = product.bom_line_ids.bom_id
            # It seems we had cache issue on archiving bom...
            used_in_bom_lines = self.env["mrp.bom.line"].search(
                [("product_id", "=", product.id)]
            )
            used_in_boms = used_in_bom_lines.bom_id.filtered(
                lambda bom: bom.type != "phantom"
            ).with_context(active_test=False)
            for bom in used_in_boms.filtered("active"):
                products = bom.product_id or bom.product_tmpl_id.product_variant_ids
                to_link = products.filtered(lambda p: not p.plan_ids)
                derivated_products |= to_link
        return derivated_products


#    def _get_default_hardware_revision(self, prototype=False):
#        revisions = self.product_tmpl_id.hardware_revision_ids.filtered(
#            lambda rec, proto=prototype: (not proto and rec.is_current_revision)
#            or (proto and rec.prototype)
#        )
#        if len(revisions) == 1:
#            return revisions
#        else:
#            return False

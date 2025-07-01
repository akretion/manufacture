# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    # for now technical field
    dmr_ids = fields.Many2many(
        "dmr",
        relation="dmr_product_rel",
        column1="product_id",
        column2="dmr_id",
        string="DMR",
    )
    linked_dmr_ids = fields.Many2many(
        "dmr",
        relation="dmr_link_product_rel",
        column1="product_id",
        column2="dmr_id",
        help="Herited DMR (from component)",
    )
    dmr_id = fields.Many2one("dmr", compute="_compute_dmr_id", store=True)

    @api.depends("dmr_ids", "linked_dmr_ids")
    def _compute_dmr_id(self):
        for product in self:
            dmr = product.dmr_ids or product.linked_dmr_ids
            product.dmr_id = dmr and dmr[0].id or False

    def _get_derivative_dmr_product(self):
        derivated_products = self.env["product.product"]
        for product in self:
            # used_in_bom = product.bom_line_ids.bom_id
            # It seems we had cache issue on archiving bom...
            used_in_bom_lines = self.env["mrp.bom.line"].search(
                [("product_id", "=", product.id)]
            )
            used_in_boms = used_in_bom_lines.bom_id.with_context(active_test=False)
            for bom in used_in_boms.filtered("active"):
                products = bom.product_id or bom.product_tmpl_id.product_variant_ids
                to_link = products.filtered(lambda p: not p.dmr_ids)
                derivated_products |= to_link
        return derivated_products

    def _get_default_dmr_revision(self, prototype=False):
        # expect recordset of 1 record or empty
        if not self:
            return self.env["dmr.revision"]
        self.ensure_one()
        dmr = self.dmr_id
        if prototype:
            return dmr.prototype_revision_id
        else:
            return dmr.current_revision_id

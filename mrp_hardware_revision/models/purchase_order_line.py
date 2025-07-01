# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    hardware_revision_id = fields.Many2one(
        "product.hardware.revision",
        compute="_compute_hardware_revision_id",
        store=True,
        readonly=False,
    )
    product_tmpl_id = fields.Many2one(
        "product.template", related="product_id.product_tmpl_id"
    )
    force_revision = fields.Boolean()
    hardware_revision_domain = fields.Binary(
        compute="_compute_hardware_revision_domain"
    )

    @api.depends("product_id", "force_revision")
    def _compute_hardware_revision_id(self):
        for pol in self:
            pol.hardware_revision_id = pol.product_id._get_default_hardware_revision(
                prototype=pol.force_revision
            )

    @api.depends("force_revision", "product_id")
    def _compute_hardware_revision_domain(self):
        for pol in self:
            if pol.force_revision:
                pol.hardware_revision_domain = [
                    ("allowed_product_ids", "in", pol.product_id.ids)
                ]
            else:
                pol.hardware_revision_domain = [
                    ("allowed_product_ids", "in", pol.product_id.ids),
                    ("is_current_revision", "=", True),
                ]

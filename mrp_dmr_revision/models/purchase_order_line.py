# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    dmr_revision_id = fields.Many2one(
        "dmr.revision",
        compute="_compute_dmr_revision_id",
        #        domain="[('allowed_product_ids', 'in', product_id), ('prototype', '=', prototype), ('is_current_revision', '!=', prototype)]",  # noqa E501
        store=True,
        readonly=False,
    )
    dmr_revision_domain = fields.Binary(compute="_compute_dmr_revision_domain")
    # Keep in editable for now, just in case... see later if we can make it readonly
    # as it computes from dmr_revision.
    #    hardware_revision_id = fields.Many2one(readonly=True)

    @api.depends("product_id", "force_revision", "dmr_revision_id")
    def _compute_hardware_revision_id(self):
        res = super()._compute_hardware_revision_id()
        for pol in self:
            if pol.product_id and pol.dmr_revision_id:
                hardware_revision = pol.dmr_revision_id.hardware_revision_ids.filtered(
                    lambda rev, line=pol: rev.plan_id == line.product_id.plan_id
                )
                pol.hardware_revision_id = hardware_revision.id
        return res

    @api.depends("product_id", "force_revision")
    def _compute_dmr_revision_id(self):
        for pol in self:
            pol.dmr_revision_id = pol.product_id._get_default_dmr_revision(
                prototype=pol.force_revision
            )

    @api.depends("force_revision", "product_id")
    def _compute_dmr_revision_domain(self):
        for pol in self:
            if pol.force_revision:
                pol.dmr_revision_domain = [
                    ("allowed_product_ids", "in", pol.product_id.ids)
                ]
            else:
                pol.dmr_revision_domain = [
                    ("allowed_product_ids", "in", pol.product_id.ids),
                    ("is_current_revision", "=", True),
                ]

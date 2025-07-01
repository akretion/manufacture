# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, exceptions, fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    dmr_revision_id = fields.Many2one(
        "dmr.revision",
        compute="_compute_dmr_revision_id",
        #        domain="[('allowed_product_ids', 'in', product_id), ('prototype', '=', prototype), ('is_current_revision', '!=', prototype)]",  # noqa E501
        store=True,
        readonly=False,
    )
    dmr_revision_domain = fields.Binary(compute="_compute_dmr_revision_domain")

    @api.depends("force_revision", "product_id")
    def _compute_dmr_revision_domain(self):
        for mo in self:
            if mo.force_revision:
                mo.dmr_revision_domain = [
                    ("allowed_product_ids", "in", mo.product_id.ids)
                ]
            else:
                mo.dmr_revision_domain = [
                    ("allowed_product_ids", "in", mo.product_id.ids),
                    ("is_current_revision", "=", True),
                ]

    @api.depends("product_id")
    def _compute_dmr_revision_id(self):
        for mo in self:
            mo.dmr_revision_id = mo.product_id._get_default_dmr_revision(
                prototype=mo.force_revision
            )

    def action_confirm(self):
        if self.product_id.dmr_id:
            if not self.dmr_revision_id:
                raise exceptions.UserError(
                    self.env._(
                        "The DMR revision is mandatory for "
                        "manufacturing order %(mo)s",
                        mo=self.name,
                    )
                )
        return super().action_confirm()

    def _set_lot_producing(self):
        self.ensure_one()
        return super(
            MrpProduction,
            self.with_context(
                default_dmr_revision_id=self.dmr_revision_id.id,
            ),
        )._set_lot_producing()

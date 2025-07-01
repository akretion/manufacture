# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, exceptions, fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    hardware_revision_id = fields.Many2one(
        "product.hardware.revision",
        compute="_compute_hardware_revision_id",
        #        domain="[('allowed_product_ids', 'in', product_id), ('prototype', '=', prototype), ('is_current_revision', '!=', prototype)]",  # noqa E501
        store=True,
        readonly=False,
    )
    force_revision = fields.Boolean()
    hardware_revision_domain = fields.Binary(
        compute="_compute_hardware_revision_domain"
    )

    @api.depends("force_revision", "product_id")
    def _compute_hardware_revision_domain(self):
        for mo in self:
            if mo.force_revision:
                mo.hardware_revision_domain = [
                    ("allowed_product_ids", "in", mo.product_id.ids)
                ]
            else:
                mo.hardware_revision_domain = [
                    ("allowed_product_ids", "in", mo.product_id.ids),
                    ("is_current_revision", "=", True),
                ]

    @api.depends("product_id")
    def _compute_hardware_revision_id(self):
        for mo in self:
            mo.hardware_revision_id = mo.product_id._get_default_hardware_revision(
                prototype=mo.force_revision
            )

    def _post_inventory(self, cancel_backorder=False):
        res = super()._post_inventory(cancel_backorder=cancel_backorder)
        for mo in self:
            mo._check_hardware_revision_consistency()
        return res

    def action_confirm(self):
        if self.product_id.plan_id:
            if not self.hardware_revision_id:
                raise exceptions.UserError(
                    self.env._(
                        "The hardware revison is mandatory for manufacturing order "
                        "%(mo)s",
                        mo=self.name,
                    )
                )
        return super().action_confirm()

    def _check_hardware_revision_consistency(self):
        self.ensure_one()
        if self.product_id.plan_id:
            same_plan_component_moves = self.move_raw_ids.filtered(
                lambda x: x.state == "done"
                and x.product_id.plan_id == self.product_id.plan_id
            )
            components_hardware_revision = (
                same_plan_component_moves.move_line_ids.lot_id.hardware_revision_id
            )
            if (
                same_plan_component_moves
                and self.hardware_revision_id != components_hardware_revision
            ):
                raise exceptions.UserError(
                    self.env._(
                        "The hardware revison of some components are not consistent"
                        " with the one of the manufacturing order %(mo)s",
                        mo=self.name,
                    )
                )

    def _set_lot_producing(self):
        self.ensure_one()
        return super(
            MrpProduction,
            self.with_context(
                default_hardware_revision_id=self.hardware_revision_id.id
            ),
        )._set_lot_producing()

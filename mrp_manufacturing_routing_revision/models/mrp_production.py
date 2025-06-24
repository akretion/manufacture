# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, exceptions, fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    manufacturing_routing_revision_id = fields.Many2one(
        "manufacturing.routing.revision",
        compute="_compute_manufacturing_routing_revision_id",
        domain="[('allowed_product_ids', 'in', product_id), ('prototype', '=', prototype), ('is_current_revision', '!=', prototype)]",  # noqa E501
        store=True,
        readonly=False,
    )
    prototype = fields.Boolean()

    @api.depends("product_id")
    def _compute_manufacturing_routing_revision_id(self):
        for mo in self:
            mo.manufacturing_routing_revision_id = (
                mo.product_id._get_default_manufacturing_routing_revision(
                    prototype=mo.prototype
                )
            )

    def action_confirm(self):
        if self.product_id.manufacturing_routing_ids:
            if not self.manufacturing_routing_revision_id:
                raise exceptions.UserError(
                    self.env._(
                        "The manufacturing routing revison is mandatory for "
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
                default_hardware_revision_id=self.hardware_revision_id.id,
                default_manufacturing_routing_revision_id=self.manufacturing_routing_revision_id.id,
            ),
        )._set_lot_producing()

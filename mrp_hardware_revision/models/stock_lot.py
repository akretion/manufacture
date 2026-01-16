# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, exceptions, fields, models


class StockLot(models.Model):
    _inherit = "stock.lot"

    hardware_revision_id = fields.Many2one(
        "product.hardware.revision",
        tracking=1,
        domain="[('allowed_product_ids', 'in', product_id)]",
    )
    prototype = fields.Boolean(compute="_compute_prototype", store=True)

    # We do not recompute from hardware_revision_id.prototype on purpose because
    # if we bought/produce a prototype, it will always stays this way, even if
    # the plan revision is adopted later.
    @api.depends("hardware_revision_id")
    def _compute_prototype(self):
        for lot in self:
            lot.prototype = lot.hardware_revision_id.prototype

    @api.constrains("product_id")
    def _check_existing_hardware_revision(self):
        for lot in self:
            if (
                lot.product_id.plan_ids or lot.product_id.linked_plan_ids
            ) and not lot.hardware_revision_id:
                raise exceptions.UserError(
                    self.env._(
                        "The hardware revision is mandatory on lot %(lot)s for "
                        "product %(product)s",
                        lot=lot.name,
                        product=lot.product_id.default_code,
                    )
                )


#    product_tmpl_id = fields.Many2one(
#        "product.template", related="product_id.product_tmpl_id"
#    )

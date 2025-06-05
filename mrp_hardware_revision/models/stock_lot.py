# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, exceptions, fields, models


class StockLot(models.Model):
    _inherit = "stock.lot"

    hardware_revision_id = fields.Many2one(
        "product.hardware.revision",
        domain="[('allowed_product_ids', 'in', product_id)]",
    )

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

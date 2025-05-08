# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductHardwareRevision(models.Model):
    _name = "product.hardware.revision"
    _description = "Product Hardware Revision"

    name = fields.Char(required=True)
    product_tmpl_id = fields.Many2one(
        "product.template", required=True, domain=[("tracking", "!=", "none")]
    )
    # product_id = fields.Many2one("product.product")
    bom_id = fields.Many2one(
        "mrp.bom", domain="[('product_tmpl_id', '=', product_tmpl_id)]"
    )
    # applicable_product_ids (other module) (which product can be associated with this revision. example if I have a product  with revision
    # and another which is the same but packaged (with OF, the one but packaged by lot of 2, etc...)
    prototype = fields.Boolean()
    generated_by_eco_id = fields.Many2one("hardware.revision.order")
    start_date = fields.Date(copy=False)
    is_current_revision = fields.Boolean(
        compute="_compute_is_current_revision", store=True
    )

    @api.depends("product_tmpl_id.hardware_revision_ids.start_date")
    def _compute_is_current_revision(self):
        for rec in self:
            if (
                rec.start_date
                and max(
                    rec.product_tmpl_id.hardware_revision_ids.filtered(
                        lambda rec: rec.start_date
                    ).mapped("start_date")
                )
                == rec.start_date
            ):
                rec.is_current_revision = True
            else:
                rec.is_current_revision = False

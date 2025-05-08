# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.fields import first


class ProductHardwareRevision(models.Model):
    _name = "product.hardware.revision"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Product Hardware Revision"
    _order = "start_date desc, name desc"

    name = fields.Char(required=True)
    plan_id = fields.Many2one("hardware.plan", required=True)
    #    product_tmpl_id = fields.Many2one(
    #        "product.template", related="product_id.product_tmpl_id")
    #    product_id = fields.Many2one("product.product", required=True, domain=[("tracking", "!=", "none")])
    allowed_product_ids = fields.Many2many(
        "product.product", compute="_compute_allowed_product_ids", store=True
    )
    bom_ids = fields.Many2many(
        "mrp.bom",
        # domain="[('product_tmpl_id', '=', product_tmpl_id), '|', ('product_id', '=', False), ('product_id', '=', product_id)]"
        readonly=True,
    )
    # applicable_product_ids (other module) (which product can be associated with
    #this revision. example if I have a product  with revision
    # and another which is the same but packaged (with OF, the one but packaged by lot
    # of 2, etc...)
    prototype = fields.Boolean()
    generated_by_eco_id = fields.Many2one("engineering.change.order")
    start_date = fields.Date(copy=False)
    is_current_revision = fields.Boolean(
        compute="_compute_is_current_revision", store=True
    )

    @api.depends("plan_id.product_ids", "plan_id.additional_product_ids")
    def _compute_allowed_product_ids(self):
        for rec in self:
            rec.allowed_product_ids = (
                rec.plan_id.product_ids | rec.plan_id.additional_product_ids
            )

    @api.depends("plan_id.revision_ids.start_date")
    def _compute_is_current_revision(self):
        for rec in self:
            revisions = rec.plan_id.revision_ids.filtered(lambda rec: rec.start_date)
            if rec.start_date and rec == first(revisions):
                rec.is_current_revision = True
            else:
                rec.is_current_revision = False


#    @api.depends("product_tmpl_id.hardware_revision_ids.start_date")
#    def _compute_is_current_revision(self):
#        for rec in self:
#            if (
#                rec.start_date
#                and max(
#                    rec.product_tmpl_id.hardware_revision_ids.filtered(
#                        lambda rec: rec.start_date
#                    ).mapped("start_date")
#                )
#                == rec.start_date
#            ):
#                rec.is_current_revision = True
#            else:
#                rec.is_current_revision = False

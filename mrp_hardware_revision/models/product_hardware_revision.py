# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, exceptions, fields, models
from odoo.fields import first


class ProductHardwareRevision(models.Model):
    _name = "product.hardware.revision"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Product Hardware Revision"
    _order = "start_date desc, name desc"
    _rec_names_search = ["name", "plan_id.name"]

    name = fields.Char(required=True)
    plan_id = fields.Many2one("hardware.plan", required=True)
    #    product_tmpl_id = fields.Many2one(
    #        "product.template", related="product_id.product_tmpl_id")
    allowed_product_ids = fields.Many2many(
        "product.product", compute="_compute_allowed_product_ids", store=True
    )
    bom_ids = fields.Many2many(
        "mrp.bom",
        readonly=True,
    )
    # applicable_product_ids (other module) (which product can be associated with
    # this revision. example if I have a product  with revision
    # and another which is the same but packaged (with OF, the one but packaged by lot
    # of 2, etc...)
    prototype = fields.Boolean()
    generated_by_eco_id = fields.Many2one("engineering.change.order")
    eco_state = fields.Selection(related="generated_by_eco_id.state")
    start_date = fields.Date(copy=False)
    is_current_revision = fields.Boolean(
        compute="_compute_is_current_revision", store=True
    )
    current_revision_id = fields.Many2one(
        "product.hardware.revision", related="plan_id.current_revision_id"
    )
    company_id = fields.Many2one(
        "res.company", related="plan_id.company_id", store=True
    )
    is_readonly = fields.Boolean(compute="_compute_is_readonly")

    _sql_constraints = [
        ("unique_plan_indice", "unique (plan_id, name)", "This revision already exists")
    ]

    # Full custom..
    @api.depends("start_date")
    def _compute_is_readonly(self):
        for rec in self:
            readonly = True
            if rec.start_date and rec.start_date < fields.Date.to_date("2026-01-01"):
                readonly = False
            rec.is_readonly = readonly

    @api.depends("plan_id", "name")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.plan_id.name} - {rec.name}"

    @api.depends("plan_id.product_ids", "plan_id.linked_product_ids")
    def _compute_allowed_product_ids(self):
        for rec in self:
            rec.allowed_product_ids = (
                rec.plan_id.product_ids | rec.plan_id.linked_product_ids
            )

    @api.depends("plan_id.revision_ids.start_date")
    def _compute_is_current_revision(self):
        for rec in self:
            revisions = rec.plan_id.revision_ids.filtered(lambda rec: rec.start_date)
            if rec.start_date and rec == first(revisions):
                rec.is_current_revision = True
            else:
                rec.is_current_revision = False

    def unlink(self):
        po_lines = self.env["purchase.order.line"].search(
            [
                ("hardware_revision_id", "in", self.ids),
                ("order_id.state", "!=", "cancel"),
            ]
        )
        if po_lines:
            used_revision_names = po_lines.hardware_revision_id.mapped("display_name")
            po_names = po_lines.order_id.mapped("name")
            raise exceptions.UserError(
                self.env._(
                    "Some revision you try to delete are already used in Purchase "
                    "orders. \nUsed Indices : %(used_revision_names)s. \n Purchase "
                    "orders concerned: %(po_names)s",
                    used_revision_names=used_revision_names,
                    po_names=po_names,
                )
            )
        return super().unlink()

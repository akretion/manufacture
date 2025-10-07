# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, exceptions, fields, models
from odoo.fields import first


class DMRRevision(models.Model):
    _name = "dmr.revision"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Device Master Record Revision"
    _order = "start_date desc, name desc"
    _rec_names_search = ["name", "dmr_id.name"]

    name = fields.Char(required=True)
    dmr_id = fields.Many2one("dmr", required=True)
    allowed_product_ids = fields.Many2many(
        "product.product", compute="_compute_allowed_product_ids", store=True
    )
    prototype = fields.Boolean()
    generated_by_eco_id = fields.Many2one("engineering.change.order")
    start_date = fields.Date(copy=False)
    is_current_revision = fields.Boolean(
        compute="_compute_is_current_revision", store=True
    )
    current_revision_id = fields.Many2one(
        "dmr.revision", related="dmr_id.current_revision_id"
    )
    hardware_revision_ids = fields.Many2many(
        "product.hardware.revision",
        relation="dmr_hardware_revision_rel",
        column1="dmr_revision_id",
        column2="hardware_revision_id",
    )
    company_id = fields.Many2one("res.company", related="dmr_id.company_id", store=True)

    _sql_constraints = [
        ("unique_dmr_revision", "unique (dmr_id, name)", "This revision already exists")
    ]

    @api.constrains("hardware_revision_ids")
    def _check_hardware_revision(self):
        for rec in self:
            plan_ids = [rev.plan_id for rev in rec.hardware_revision_ids]
            if len(plan_ids) != len(set(plan_ids)):
                raise exceptions.UserError(
                    self.env._(
                        "A DMR revision can't be related to multiple version of a "
                        "same plan"
                    )
                )

    @api.depends("dmr_id", "name")
    @api.depends_context("product_id")
    def _compute_display_name(self):
        for rec in self:
            display_name = f"{rec.dmr_id.name} - {rec.name}"
            if self.env.context.get("product_id"):
                product = self.env["product.product"].browse(
                    self.env.context["product_id"]
                )
                if product.plan_id:
                    hw_rev = rec.hardware_revision_ids.filtered(
                        lambda rev, prd=product: prd in rev.allowed_product_ids
                    )
                    if len(hw_rev) == 1:
                        display_name = f"{display_name} ({hw_rev.display_name})"
            rec.display_name = display_name

    @api.depends("dmr_id.product_ids")
    def _compute_allowed_product_ids(self):
        for rec in self:
            rec.allowed_product_ids = (
                rec.dmr_id.product_ids | rec.dmr_id.linked_product_ids
            )

    @api.depends("dmr_id.revision_ids.start_date")
    def _compute_is_current_revision(self):
        for rec in self:
            revisions = rec.dmr_id.revision_ids.filtered(lambda rec: rec.start_date)
            if rec.start_date and rec == first(revisions):
                rec.is_current_revision = True
            else:
                rec.is_current_revision = False

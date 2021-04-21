# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class MrpRouting(models.Model):
    _name = "mrp.routing"
    _description = "Routings"

    name = fields.Char(required=True)
    active = fields.Boolean(
        "Active",
        default=True,
        help="If the active field is set to False, it will allow you to hide the "
        "routing without removing it.",
    )
    code = fields.Char(
        "Reference", copy=False, default=lambda self: _("New"), readonly=True
    )
    note = fields.Text("Description")
    operation_ids = fields.One2many(
        "mrp.routing.workcenter", "routing_id", "Operations", copy=True
    )
    company_id = fields.Many2one(
        "res.company", "Company", default=lambda self: self.env.company
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "code" not in vals or vals["code"] == _("New"):
                vals["code"] = self.env["ir.sequence"].next_by_code("mrp.routing") or _(
                    "New"
                )
        return super().create(vals_list)

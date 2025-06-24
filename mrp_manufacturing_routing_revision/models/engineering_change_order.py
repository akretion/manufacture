# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, exceptions, fields, models


class EngineeringChangeOrder(models.Model):
    _inherit = "engineering.change.order"

    plan_ids = fields.Many2many(compute="_compute_plan_ids", store=True, readonly=False)
    manufacturing_routing_id = fields.Many2one("manufacturing.routing")
    new_manufacturing_routing_revision_ids = fields.One2many(
        "manufacturing.routing.revision", "generated_by_eco_id"
    )
    hardware_revison_update = fields.Boolean()

    @api.depends("manufacturing_routing_id")
    def _compute_plan_ids(self):
        for rec in self:
            if rec.manufacturing_routing_id:
                plans = rec.manufacturing_routing_ids.product_ids.plan_ids
                rec.plan_ids = plans.ids

    def action_confirm(self):
        self.ensure_one()
        res = super().action_confirm()
        if self.manufacturing_routing_id:
            vals = {
                "start_date": False,
                "prototype": True,
                "name": "prototype",
                "generated_by_eco_id": self.id,
            }
            if self.manufacturing_routing_id.current_revision_id:
                self.manufacturing_routing_id.current_revision_id.copy(vals)
            else:
                vals["manufacturing_revision_id"] = self.manufacturing_routing_id.id
                self.env["manfacturing_routing_revision"].create(vals)
        return res

    def action_done(self):
        res = super().action_done()
        if any(
            [
                rev.name == "prototype"
                for rev in self.new_manufacturing_routing_revision_ids
            ]
        ):
            raise exceptions.UserError(
                self.env._(
                    "You can't validate this ECO yet because not all manufacturing "
                    "routing revisions have a number"
                )
            )
        self.new_manufacturing_routing_revision_ids.write(
            {"prototype": False, "start_date": fields.Date.today()}
        )
        return res

    def action_view_new_manufacturing_routing_revision(self):
        self.ensure_one()
        revisions = self.new_manufacturing_routing_revision_ids
        action = self.env["ir.actions.actions"]._for_xml_id(
            "mrp_hardware_revision.action_manufacturing_routing_revision"
        )
        if len(revisions) > 1:
            action["domain"] = [("id", "in", revisions.ids)]
        elif revisions:
            form_view = [
                (
                    self.env.ref(
                        "mrp_hardware_revision.manufacturing_routing_revision_form_view"
                    ).id,
                    "form",
                )
            ]
            action["res_id"] = revisions.id
            if "views" in action:
                action["views"] = form_view + [
                    (state, view) for state, view in action["views"] if view != "form"
                ]
            else:
                action["views"] = form_view
        return action

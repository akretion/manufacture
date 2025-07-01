# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, exceptions, fields, models
from odoo.fields import Command


class EngineeringChangeOrder(models.Model):
    _inherit = "engineering.change.order"

    dmr_ids = fields.Many2many(
        "dmr", compute="_compute_dmr_ids", readonly=False, store=True
    )
    new_dmr_revision_ids = fields.One2many("dmr.revision", "generated_by_eco_id")

    def action_draft(self):
        res = super().action_draft()
        self.new_dmr_revision_ids.unlink()
        return res

    @api.depends("plan_ids")
    def _compute_dmr_ids(self):
        for rec in self:
            if rec.plan_ids:
                dmrs = rec.plan_ids.product_ids.dmr_ids
                rec.dmr_ids = dmrs.ids

    def _get_boms_to_update(self):
        boms = super()._get_boms_to_update()
        domain = self.env["mrp.bom"]._bom_find_domain(self.dmr_ids.product_ids)
        boms |= self.env["mrp.bom"].search(domain)
        return boms

    def action_confirm(self):
        res = super().action_confirm()
        for dmr in self.dmr_ids:
            vals = {
                "start_date": False,
                "prototype": True,
                "name": "prototype",
                "generated_by_eco_id": self.id,
            }
            if dmr.current_revision_id:
                dmr.current_revision_id.copy(vals)
            else:
                vals["dmr_id"] = dmr.id
                self.env["dmr.revision"].create(vals)
        return res

    def _check_plan_consistency(self):
        self.ensure_one()
        if self.plan_ids:
            required_dmrs = self.plan_ids.product_ids.dmr_id
            if set(required_dmrs).intersection(self.dmr_ids) != set(required_dmrs):
                raise exceptions.UserError(
                    self.env._(
                        "At least one DMR concerned by the plans changes is not "
                        "present in this ECO."
                    )
                )

    def action_done(self):
        res = super().action_done()
        if any([rev.name == "prototype" for rev in self.new_dmr_revision_ids]):
            raise exceptions.UserError(
                self.env._(
                    "You can't validate this ECO yet because not all DMR "
                    "revisions have a number"
                )
            )
        self._check_plan_consistency()
        self.new_dmr_revision_ids.write(
            {"prototype": False, "start_date": fields.Date.today()}
        )
        for dmr_rev in self.new_dmr_revision_ids:
            dmr_plans = dmr_rev.dmr_id.product_ids.plan_id
            if self.plan_ids:
                hardware_revisions = self.new_hardware_revision_ids.filtered(
                    lambda hw_rev, plans=dmr_plans: hw_rev.plan_id in plans
                )
            else:
                hardware_revisions = dmr_plans.current_revision_id
            dmr_rev.write(
                {"hardware_revision_ids": [Command.set(hardware_revisions.ids)]}
            )
        return res

    def action_view_new_dmr_revision(self):
        self.ensure_one()
        revisions = self.new_dmr_revision_ids
        action = self.env["ir.actions.actions"]._for_xml_id(
            "mrp_dmr_revision.action_dmr_revision"
        )
        if len(revisions) > 1:
            action["domain"] = [("id", "in", revisions.ids)]
        elif revisions:
            form_view = [
                (
                    self.env.ref("mrp_dmr_revision.dmr_revision_form_view").id,
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

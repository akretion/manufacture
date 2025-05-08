# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, exceptions, fields, models


class EngineeringChangeOrder(models.Model):
    _name = "engineering.change.order"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Engineering Change Order"

    name = fields.Char(required=True)
    plan_ids = fields.Many2many("hardware.plan")
    new_bom_ids = fields.Many2many("mrp.bom")
    new_bom_count = fields.Integer(compute="_compute_new_bom_count")
    #    hardware_revision_id = fields.Many2one("product.hardware.revision", required=True)
    new_hardware_revision_ids = fields.One2many(
        "product.hardware.revision", "generated_by_eco_id"
    )
    state = fields.Selection(
        [
            ("1-draft", "New"),
            ("2-ongoing", "Ongoing"),
            ("3-prototype", "Prototype"),
            ("4-done", "Done"),
        ],
        default="1-draft",
    )
    bom_update = fields.Boolean()
    planned_start_date = fields.Date()
    planned_end_date = fields.Date()
    start_date = fields.Date()
    end_date = fields.Date()
    note = fields.Text()

    def _generate_boms(self):
        self.ensure_one()
        if self.state == "done":
            raise
        self.new_bom_ids.unlink()
        if not self.bom_update:
            return
        domain = self.env["mrp.bom"]._bom_find_domain(self.plan_ids.product_ids)
        boms = self.env["mrp.bom"].search(domain)
        new_boms = self.env["mrp.bom"]
        for bom in boms:
            new_boms |= bom.copy(
                {"eco_id": self.id, "active": False, "previous_bom_id": bom.id}
            )
        if new_boms:
            self.write({"new_bom_ids": [Command.set(new_boms.ids)]})

    def _compute_new_bom_count(self):
        for rec in self:
            rec.new_bom_count = len(rec.with_context(active_test=False).new_bom_ids)

    def action_confirm(self):
        self.ensure_one()
        self.state = "2-ongoing"
        self.start_date = fields.Date.today()
        self._generate_boms()
        new_revisions = self.env["product.hardware.revision"]
        for plan in self.plan_ids:
            vals = {
                "start_date": False,
                "prototype": True,
                "name": "/",
                "generated_by_eco_id": self.id,
            }
            if plan.current_revision_id:
                new_revisions |= plan.current_revision_id.copy(vals)
            else:
                vals["plan_id"] = plan.id
                new_revisions |= self.env["product.hardware.revision"].create(vals)

    def validate_prototype(self):
        self.ensure_one()
        self.write({"state": "3-prototype"})

    def action_done(self):
        self.ensure_one()
        if self.bom_update:
            domain = self.env["mrp.bom"]._bom_find_domain(self.plan_ids.product_ids)
            active_boms = self.env["mrp.bom"].search(domain)
            boms_to_active = self.with_context(active_test=False).new_bom_ids
            boms_to_archive = boms_to_active.previous_bom_id
            # TODO check what to do with these cases
            if boms_to_archive - active_boms:
                raise exceptions.UserError(
                    self.env._(
                        "Some Bom modified by thos ECO are not active %(boms)s",
                        boms=(boms_to_archive - active_boms).ids,
                    )
                )
            elif active_boms - boms_to_archive:
                raise exceptions.UserError(
                    self.env._(
                        "Some active BOMs were not taken into account by current eco:  %(boms)s",
                        boms=(active_boms - boms_to_archive).ids,
                    )
                )
            boms_to_archive.write({"active": False})
            boms_to_active.write({"active": True})
        self.state = "4-done"
        self.end_date = fields.Date.today()
        if any([rev.name == "/" for rev in self.new_hardware_revision_ids]):
            raise exceptions.UserError(
                self.env._(
                    "You can't validate this ECO yet because not all revisions have a number"
                )
            )
        self.new_hardware_revision_ids.write(
            {"prototype": False, "start_date": fields.Date.today()}
        )

    def action_view_new_revision(self):
        self.ensure_one()
        revisions = self.new_hardware_revision_ids
        action = self.env["ir.actions.actions"]._for_xml_id(
            "mrp_hardware_revision.action_product_hardware_revision"
        )
        if len(revisions) > 1:
            action["domain"] = [("id", "in", revisions.ids)]
        elif revisions:
            form_view = [
                (
                    self.env.ref(
                        "mrp_hardware_revision.product_hardware_revision_form_view"
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

    def action_view_new_boms(self):
        self.ensure_one()
        boms = self.with_context(active_test=False).new_bom_ids
        action = self.env["ir.actions.actions"]._for_xml_id("mrp.mrp_bom_form_action")
        ctx = self.env.context.copy()
        ctx["active_test"] = False
        action["context"] = ctx
        if len(boms) > 1:
            action["domain"] = [("id", "in", boms.ids)]
        elif boms:
            form_view = [
                (
                    self.env.ref("mrp.mrp_bom_form_view").id,
                    "form",
                )
            ]
            action["res_id"] = boms.id
            if "views" in action:
                action["views"] = form_view + [
                    (state, view) for state, view in action["views"] if view != "form"
                ]
            else:
                action["views"] = form_view
        return action

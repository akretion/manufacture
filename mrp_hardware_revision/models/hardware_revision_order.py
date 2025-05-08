# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import exceptions, fields, models


class HardwareRevisionOrder(models.Model):
    _name = "hardware.revision.order"
    _description = "Hardware Revision Order"

    name = fields.Char(required=True)
    hardware_revision_id = fields.Many2one("product.hardware.revision", required=True)
    new_hardware_revision_id = fields.Many2one("product.hardware.revision")
    state = fields.Selection(
        [("draft", "New"), ("ongoing", "Ongoing"), ("done", "Done")], default="draft"
    )
    bump_revision = fields.Boolean()
    planned_start_date = fields.Date()
    planned_end_date = fields.Date()
    start_date = fields.Date()
    end_date = fields.Date()
    note = fields.Text()

    def action_confirm(self):
        for order in self.filtered(lambda rec: rec.state == "draft"):
            order.state = "ongoing"
            order.start_date = fields.Date.today()
            if order.bump_revision:
                new_bom = False
                if order.hardware_revision_id.bom_id:
                    new_bom = order.hardware_revision_id.bom_id.copy({"active": False})
                new_rev = order.hardware_revision_id.copy(
                    {
                        "generated_by_eco_id": order.id,
                        "name": "/",
                        "prototype": True,
                        "bom_id": new_bom,
                    }
                )
                order.new_hardware_revision_id = new_rev

    def action_done(self):
        for order in self.filtered(lambda rec: rec.state == "ongoing"):
            order.state = "done"
            order.end_date = fields.Date.today()
            if order.bump_revision:
                if order.new_hardware_revision_id.name == "/":
                    raise exceptions.UserError(
                        "You can't validate the revision for '%s' because its revision number has not been set yet"
                        % order.new_hardware_revision_id.product_tmpl_id.name
                    )
                order.new_hardware_revision_id.prototype = False
                order.new_hardware_revision_id.bom_id.active = True
                order.new_hardware_revision_id.start_date = fields.Date.today()
                order.hardware_revision_id.bom_id.active = False

    def action_view_new_revision(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "mrp_hardware_revision.action_product_hardware_revision"
        )
        form_view = [
            (
                self.env.ref(
                    "mrp_hardware_revision.product_hardware_revision_form_view"
                ).id,
                "form",
            )
        ]
        action["views"] = form_view
        action["res_id"] = self.new_hardware_revision_id.id
        return action

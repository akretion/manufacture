# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, exceptions, fields, models


class RawMaterialSwap(models.TransientModel):
    _name = "raw.material.swap"
    _description = "Wizard to replace a raw material by another inside a MO"

    production_ids = fields.Many2many(
        "mrp.production",
        string="Manufacturing Orders",
        compute="_compute_production_ids",
        store=True,
        default=lambda c: c.env.context.get("active_ids"),
    )
    move_raw_ids = fields.Many2many(
        "stock.move", string="Components", compute="_compute_production_ids", store=True
    )
    product_id = fields.Many2one("product.product", required=True)
    product_replacement_id = fields.Many2one("product.product", required=True)

    @api.depends("product_id")
    def _compute_production_ids(self):
        mo_ids = []
        move_raw_ids = []
        active_mo_ids = self.env.context.get("active_ids", [])
        if self.product_id:
            for mo in self.env["mrp.production"].browse(active_mo_ids):
                for move in mo.move_raw_ids.filtered(
                    lambda m: m.state not in ("done", "cancel")
                ):
                    if move.product_id == self.product_id:
                        mo_ids.append(mo.id)
                        move_raw_ids.append(move.id)
            self.production_ids = mo_ids
            self.move_raw_ids = move_raw_ids
        else:
            self.production_ids = active_mo_ids
            self.move_raw_ids = []

    def switch_product(self):
        prd_patern_id = self.product_id
        prd_replacement_id = self.product_replacement_id
        if prd_patern_id.uom_id != prd_replacement_id.uom_id:
            raise exceptions.UserError(
                _(
                    "The unit of measure of the replcement component is not the same as "
                    "the component to replace. Please chose a component with same "
                    "unit of measure"
                )
            )

        # Does not seem essential. We could check if all have the same BOM
        # or same product_tmpl_id but it seems to restrictive to me.
        #        res = self.production_ids.mapped("routing_id.id")
        #        if len(res) > 1:
        #            raise exceptions.ValidationError(
        #                _("Routing are different," + " select same type
        # of manufactoring order")
        #            )

        wrong_state_mos = self.env["mrp.production"].search(
            [
                ("state", "in", ["cancel", "done"]),
                ("id", "in", self.env.context.get("active_ids", [])),
            ]
        )
        ls_of_state = wrong_state_mos.mapped("name")
        if ls_of_state:
            raise exceptions.UserError(
                _("Manufacturing orders %s are done or canceled" % (ls_of_state))
            )

        raw_moves = self.move_raw_ids

        # Do the swap
        for move in raw_moves:
            # do not keep reservation made witl old product if any
            if move.reserved_availability:
                move._do_unreserve()
            # replace the product in stock move selected
            move.write({"product_id": prd_replacement_id})
            move.raw_material_production_id.message_post(
                body=_("switch product %s to %s.")
                % (
                    self.product_id.default_code,
                    self.product_replacement_id.default_code,
                )
            )

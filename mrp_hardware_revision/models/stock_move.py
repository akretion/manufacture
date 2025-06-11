# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, exceptions, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_hardware_revision(self):
        self.ensure_one()
        return self.purchase_line_id.hardware_revision_id

    # seems better to not copy this field except when a move is split, because a move
    # can be copied in multiple different occasions and could even be copied with a
    # different product...
    restrict_hardware_revision_id = fields.Many2one(
        "product.hardware.revision",
        string="Restrict hw revision",
        copy=False,
        index=True,
        compute="_compute_restrict_hardware_revision_id",
        store=True,
        readonly=False,
    )

    @api.depends("raw_material_production_id.hardware_revision_id")
    def _compute_restrict_hardware_revision_id(self):
        for move in self:
            mo_revision = move.raw_material_production_id.hardware_revision_id
            if mo_revision and move.product_id.plan_id == mo_revision.plan_id:
                move.restrict_hardware_revision_id = mo_revision.id

    def _prepare_procurement_values(self):
        vals = super()._prepare_procurement_values()
        vals["restrict_hardware_revision_id"] = self.restrict_hardware_revision_id.id
        return vals

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        distinct_fields = super()._prepare_merge_moves_distinct_fields()
        distinct_fields.append("restrict_hardware_revision_id")
        return distinct_fields

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        vals = super()._prepare_move_line_vals(
            quantity=quantity, reserved_quant=reserved_quant
        )
        if self.restrict_hardware_revision_id:
            if (
                "lot_id" in vals
                and vals["lot_id"] is not False
                and self.env["stock.lot"].browse(vals["lot_id"]).hardware_revision_id
                != self.restrict_hardware_revision_id
            ):
                raise exceptions.UserError(
                    self.env._(
                        "Inconsistencies between reserved quant and hardware revision "
                        "restriction on stock move"
                    )
                )
        return vals

    def _get_available_quantity(
        self,
        location_id,
        lot_id=None,
        package_id=None,
        owner_id=None,
        strict=False,
        allow_negative=False,
    ):
        self.ensure_one()
        if self.restrict_hardware_revision_id:
            self = self.with_context(hw_revision=self.restrict_hardware_revision_id)
        return super()._get_available_quantity(
            location_id,
            lot_id=lot_id,
            package_id=package_id,
            owner_id=owner_id,
            strict=strict,
            allow_negative=allow_negative,
        )

    def _update_reserved_quantity(
        self,
        need,
        location_id,
        lot_id=None,
        package_id=None,
        owner_id=None,
        strict=True,
    ):
        self.ensure_one()
        if self.restrict_hardware_revision_id:
            self = self.with_context(hw_revision=self.restrict_hardware_revision_id)
        return super()._update_reserved_quantity(
            need,
            location_id,
            lot_id=lot_id,
            package_id=package_id,
            owner_id=owner_id,
            strict=strict,
        )

    def _split(self, qty, restrict_partner_id=False):
        vals_list = super()._split(qty, restrict_partner_id=restrict_partner_id)
        if vals_list and self.restrict_hardware_revision_id:
            vals_list[0]["restrict_hardware_revision_id"] = (
                self.restrict_hardware_revision_id.id
            )
        return vals_list

    def _action_done(self, cancel_backorder=False):
        res = super()._action_done(cancel_backorder=cancel_backorder)
        self._check_lot_consistent_with_hw_restriction()
        return res

    def _check_lot_consistent_with_hw_restriction(self):
        """
        Check that the lot set on move lines
        has the same hardware revision as the restricted hw set on the move
        """
        for move in self:
            if not (move.restrict_hardware_revision_id and move.move_line_ids):
                continue
            move_line_hw_revision = move.mapped(
                "move_line_ids.lot_id.hardware_revision_id"
            )
            if move.restrict_hardware_revision_id != move_line_hw_revision:
                move_restrict_rev = move.restrict_hardware_revision_id
                raise exceptions.UserError(
                    self.env._(
                        "The lot(s) %(move_line_hw_revision)s being moved is "
                        "inconsistent with the restriction on "
                        "hardware_revision %(move_restrict_hw_revision)s set on the "
                        "move",
                        move_line_hw_revision=", ".join(
                            move_line_hw_revision.mapped("display_name")
                        ),
                        move_restrict_hw_revision=move_restrict_rev.display_name,
                    )
                )

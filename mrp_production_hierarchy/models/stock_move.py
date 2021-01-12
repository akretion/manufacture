# Copyright (C) 2020 - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, api, _, fields
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero


class StockMove(models.Model):
    _inherit = "stock.move"

    sub_production_id = fields.Many2one(
        string="Sub-manufacturing order",
        comodel_name="mrp.production",
        compute="_compute_sub_production_id",
        help="Sub-manufacturing Order making this raw material to be consumed",
    )

    delivery_picking_id = fields.Many2one(
        string="Delivery picking",
        comodel_name="stock.picking",
        compute="_compute_delivery_picking_id",
        help="Related picking delivering the product to be consumed to the "
        "pre-production location",
    )

    css_class = fields.Char(
        string="CSS class",
        compute="_compute_css_class",
        help="Bootstrap CSS class used in hierarchy report to inform about the "
        "'stock.move' progress",
    )

    @api.depends("move_orig_ids")
    def _compute_delivery_picking_id(self):
        for move in self:
            delivery_picking_id = move.move_orig_ids.mapped("picking_id")
            if len(delivery_picking_id) > 1:
                raise UserError(
                    _(
                        "We found more than one Picking delivering the product "
                        "'%s' " % move.product_id.display_name
                    )
                )
            else:
                move.delivery_picking_id = delivery_picking_id

    @api.depends("product_id", "raw_material_production_id")
    def _compute_sub_production_id(self):
        for move in self:
            sub_production_id = self.env["mrp.production"].search(
                [
                    ("product_id", "=", move.product_id.id),
                    ("parent_id", "=", move.raw_material_production_id.id),
                ]
            )
            if len(sub_production_id) > 1:
                raise UserError(
                    _(
                        "You cannot have more than one Sub-manfacturing Order to "
                        "produce the raw material '%s'." % move.product_id.display_name
                    )
                )
            else:
                move.sub_production_id = sub_production_id

    @api.depends("is_done", "quantity_done", "product_uom_qty", "reserved_availability")
    def _compute_css_class(self):
        """Mimic the decorations flags in move_raw_ids tree in 'mrp.production' """
        dp = self.env["decimal.precision"].precision_get("Product Unit of Measure")
        for move in self:
            # decoration-muted="is_done"
            # decoration-warning="quantity_done - product_uom_qty &gt; 0.0001"
            # decoration-success="not is_done and quantity_done - product_uom_qty &lt; 0.0001"
            # decoration-danger="not is_done and reserved_availability &lt; product_uom_qty and product_uom_qty - reserved_availability &gt; 0.0001"
            qty_init = move.product_uom_qty
            qty_done = move.quantity_done
            qty_reserved = move.reserved_availability

            if move.is_done:
                move.css_class = "text-muted"
            if float_compare(qty_init, qty_done, precision_digits=dp) > 0:
                move.css_class = "text-warning"
            if (
                not move.is_done
                and float_compare(qty_init, qty_reserved, precision_digits=dp) == 0
            ):
                move.css_class = "text-success"
            if (
                not move.is_done
                and float_compare(qty_init, qty_reserved, precision_digits=dp) > 0
                and float_compare(qty_init, qty_done, precision_digits=dp) > 0
            ):
                move.css_class = "text-danger"

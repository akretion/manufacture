# -*- coding: utf-8 -*-
# Copyright 2019 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api
from odoo.tools import float_compare, float_round


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def _prepare_move_split_vals(self, defaults):
        defaults = super(StockMove, self)._prepare_move_split_vals(defaults)
        if self.raw_material_production_id:
            production = self.raw_material_production_id
            quantity = defaults['product_uom_qty']
            original_quantity = (
                production.product_qty - production.qty_produced) or 1.0
            factor = quantity / original_quantity
            defaults['unit_factor'] = factor
        return defaults

    @api.multi
    def split(self, qty, restrict_lot_id=False, restrict_partner_id=False):
        res = super(StockMove, self).split(
            qty=qty, restrict_lot_id=restrict_lot_id,
            restrict_partner_id=restrict_partner_id)
        for move in self:
            production = move.raw_material_production_id
            for all_raw in production.move_raw_ids.filtered(
                lambda x: x.state not in ('cancel', 'done') and
                    x.product_id == move.product_id
            ):
                # recalc unit factor because we may have added moves
                original_quantity = (
                    production.product_qty - production.qty_produced) or 1.0
                all_raw.unit_factor = (
                    all_raw.product_uom_qty / original_quantity)

        return res

# -*- coding: utf-8 -*-
# Copyright 2019 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def _prepare_move_split_vals(self, defaults):
        defaults = super(StockMove, self)._prepare_move_split_vals(defaults)
        quantity = defaults['product_uom_qty']
        production = self.raw_material_production_id
        factor = quantity / (production.product_qty - production.qty_produced)
        defaults['unit_factor'] = factor
        return defaults

    @api.multi
    def split(self, qty, restrict_lot_id=False, restrict_partner_id=False):
        res = super(StockMove, self).split(
            qty=qty, restrict_lot_id=restrict_lot_id,
            restrict_partner_id=restrict_partner_id)
        for move in self:
            production = move.raw_material_production_id
            move.unit_factor = move.product_uom_qty / (
                production.product_qty - production.qty_produced)
        return res

from odoo import models


class MrpProduction(models.Model):
    _name = "mrp.production"
    _inherit = "mrp.production"

    def create(self, production_vals_list):
        res = super(
            MrpProduction, self.with_context(use_input_line_values_cache=True)
        ).create(production_vals_list)

        for rec in res:
            if rec.lot_producing_id and rec.lot_producing_id.input_line_id:
                rec.lot_producing_id.input_line_id._clear_cache_input_line_values()

        return res

    def _get_moves_raw_values(self):
        self.ensure_one()
        res = True
        if self.lot_producing_id and self.lot_producing_id.input_line_id:
            res = super(
                MrpProduction,
                self.with_context(input_line_id=self.lot_producing_id.input_line_id.id),
            )._get_moves_raw_values()
        else:
            res = super()._get_moves_raw_values()
        return res

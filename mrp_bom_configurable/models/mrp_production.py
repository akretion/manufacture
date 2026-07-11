from odoo import models


class MrpProduction(models.Model):
    _name = "mrp.production"
    _inherit = "mrp.production"

    def create(self, production_vals_list):
        res = super(
            MrpProduction, self.with_context(use_product_config_values_cache=True)
        ).create(production_vals_list)

        for rec in res:
            if rec.lot_producing_ids and rec.lot_producing_ids[0].product_config_id:
                rec.lot_producing_ids.product_config_id._clear_cache_product_config_values()

        return res

    def _get_moves_raw_values(self):
        self.ensure_one()
        res = True
        if self.lot_producing_ids and self.lot_producing_ids[0].product_config_id:
            res = super(
                MrpProduction,
                self.with_context(
                    product_config_id=self.lot_producing_ids[0].product_config_id.id
                ),
            )._get_moves_raw_values()
        else:
            res = super()._get_moves_raw_values()
        return res

    def _compute_move_raw_ids(self):
        """This method is required to remove useless raw components"""
        super()._compute_move_raw_ids()
        for production in self:
            product_config = production._get_product_config()
            if not product_config:
                continue
            to_skip = []
            for raw in production.move_raw_ids:
                if raw.bom_line_id:
                    res = raw.bom_line_id._should_skip_bom_line(product_config)
                    if res:
                        to_skip.append(raw.id)
            if to_skip:
                self.env["stock.move"].browse(to_skip).unlink()

    def _get_product_config(self):
        return self.sale_line_id.lot_id.product_config_id

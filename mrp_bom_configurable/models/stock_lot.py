from odoo import fields, models


class StockLot(models.Model):
    _name = "stock.lot"
    _inherit = "stock.lot"

    product_config_id = fields.Many2one(comodel_name="product.config")

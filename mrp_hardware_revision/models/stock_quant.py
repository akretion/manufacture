# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    hardware_revision_id = fields.Many2one(
        "product.hardware.revision",
        related="lot_id.hardware_revision_id",
        store=True,
        index="btree",
    )

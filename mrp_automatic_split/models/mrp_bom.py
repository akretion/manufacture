# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    batch_quantity = fields.Float(
        default=0.0,
        help="Automatically created manufacturing order for this BOM will be "
        "splitted according to this quantity.\n 0 means the whole quantity will "
        "be kept.",
    )

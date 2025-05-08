# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    hardware_revision_id = fields.Many2one(
        "product.hardware.revision",
        compute="_compute_hardware_revision_id",
        store=True,
        readonly=False,
    )

    @api.depends("product_id")
    def _compute_hardware_revision_id(self):
        for mo in self:
            mo.hardware_revision_id = mo.product_id._get_default_hardware_revision()

# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    hardware_revision_id = fields.Many2one(
        "product.hardware.revision",
        compute="_compute_hardware_revision_id",
        domain="[('allowed_product_ids', 'in', product_id), ('prototype', '=', prototype), ('is_current_revision', '!=', prototype)]",
        store=True,
        readonly=False,
    )
    prototype = fields.Boolean()

    @api.depends("product_id")
    def _compute_hardware_revision_id(self):
        for mo in self:
            mo.hardware_revision_id = mo.product_id._get_default_hardware_revision()

# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    plan_id = fields.Many2one(
        "hardware.plan", related="product_variant_ids.plan_id", store=True
    )
    current_revision_id = fields.Many2one(
        "product.hardware.revision", related="plan_id.current_revision_id"
    )

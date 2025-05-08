# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ProductTemplate(models.Model):
    _inherit = "product.template"


#    hardware_revision_ids = fields.One2many(
#        "product.hardware.revision", "product_tmpl_id"
#    )

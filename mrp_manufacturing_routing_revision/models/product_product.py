# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.fields import first


class ProductProduct(models.Model):
    _inherit = "product.product"

    # for now technical field
    manufacturing_routing_ids = fields.Many2many(
        "manufacturing.routing",
        relation="manufacturing_routing_product_rel",
        column1="product_id",
        column2="manufacturing_routing_id",
        string="Manufacturing Routing",
    )

    def _get_default_manufacturing_routing_revision(self, prototype=False):
        # expect recordset of 1 record or empty
        if not self:
            return self.env["manufacturing.routing.version"]
        self.ensure_one()
        rev = first(self.manufacturing_routing_ids)
        if prototype:
            return rev.prototype_revision_id
        else:
            return rev.current_revision_id

# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _get_default_hardware_revision(self, prototype=False):
        # expect recordset of 1 record or empty
        plan = self.env["hardware.plan"].search(
            [
                "|",
                ("product_ids", "in", self.ids),
                ("additional_product_ids", "in", self.ids),
            ]
        )
        if prototype:
            return plan.prototype_revision_id
        else:
            return plan.current_revision_id


#    def _get_default_hardware_revision(self, prototype=False):
#        revisions = self.product_tmpl_id.hardware_revision_ids.filtered(
#            lambda rec, proto=prototype: (not proto and rec.is_current_revision)
#            or (proto and rec.prototype)
#        )
#        if len(revisions) == 1:
#            return revisions
#        else:
#            return False

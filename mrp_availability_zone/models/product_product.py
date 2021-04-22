# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.tools.float_utils import float_round


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _get_product_mrp_reserved(self):
        # In MRP context, we do not use Odoo native reservation. So in order to know the
        # available qty for reservation, we do not look on quants, but on assigned
        # stock moves.

        domain_products = [("product_id", "in", self.ids)]
        domain_move_out_assigned = []
        _dummy1, _dummy2, domain_move_out_loc = self._get_domain_locations()
        domain_move_out_assigned += [("state", "=", ("assigned"))] + domain_products

        if self.env.context.get("owner_id"):
            owner_domain = ("restrict_partner_id", "=", self.env.context["owner_id"])
            domain_move_out_assigned.append(owner_domain)

        domain_move_out_assigned += domain_move_out_loc
        moves_out = self.env["stock.move"].read_group(
            domain_move_out_assigned, ["product_id", "product_qty"], ["product_id"]
        )

        moves_out = dict(
            map(lambda x: (x["product_id"][0], x["product_qty"]), moves_out)
        )
        res = {}
        for product in self:
            id = product.id
            outgoing_reserved_qty = float_round(
                moves_out.get(id, 0.0), precision_rounding=product.uom_id.rounding
            )
            res[id] = outgoing_reserved_qty
        return res

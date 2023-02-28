import logging

from odoo import api, fields, models

logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def action_bom_vendor_price(self):
        templates = self.filtered(
            lambda t: t.product_variant_count == 1 and t.bom_count > 0
        )
        if templates:
            return templates.mapped("product_variant_id").action_bom_vendor_price()


class ProductProduct(models.Model):
    _inherit = "product.product"

    future_cost = fields.Float(
        groups="mrp.group_mrp_user",
        readonly=True,
        help="Cost based on bom and vendor price (cost used in next purchase order "
        "of raw material)",
    )
    previous_cost = fields.Float(
        groups="mrp.group_mrp_user",
        readonly=True,
        string="Old cost",
        help="Previous vendor price stored for history purpose",
    )
    last_cost = fields.Date(
        string="Last Cost",
        readonly=True,
        groups="mrp.group_mrp_user",
    )
    vendor_price_id = fields.Many2one(
        comodel_name="product.supplierinfo",
        string="Vendor price line",
        groups="mrp.group_mrp_user",
        help="Main vendor price used to compute",
    )
    vendor_price_info = fields.Text(compute="_compute_price_info")

    def _compute_price_info(self):
        for rec in self:
            info = ""
            if rec.vendor_price_id:
                vals = {
                    "vendor": rec.vendor_price_id.name.name,
                    "price": rec.vendor_price_id.price,
                    "min_qty": rec.vendor_price_id.price,
                }
                info = (
                    "%(vendor)s\nPrice: %(price)s\nMin. qty: %(min_qty)s" % vals
                )
            rec.vendor_price_info = info

    def action_bom_vendor_price(self):
        for product in self:
            bom = self.env["mrp.bom"]._bom_find(product=product)
            if bom:
                bom.product_tmpl_id.product_variant_ids[
                    0
                ].future_cost = bom._compute_cost_with_vendor_price()

    def set_vendor_price(self):
        product_count = 0
        for product in self:
            quantity = 0
            if product.seller_ids:
                # if quantity is not provided seller_ids with quantities
                # can't be selected : fixed in v15 (testing if qty is none)
                # here is a minimal behavior
                quantity = product.seller_ids[0].min_qty
            # You may change vendor_info selection
            # overiding _select_seller() according to the context
            vendor_info = product.with_context(
                self._get_ctx_vendor_price_case()
            )._select_seller(uom_id=product.uom_id, quantity=quantity)
            vals = {}
            if vendor_info:
                if vendor_info.price != product.future_cost:
                    vals["previous_cost"] = product.future_cost
                    vals["future_cost"] = vendor_info.price
                    vals["last_cost"] = fields.Date.today()
                    product_count += 1
                if vendor_info != product.vendor_price_id:
                    vals["vendor_price_id"] = vendor_info.id
            elif product.vendor_price_id:
                vals["vendor_price_id"] = False
                vals["future_cost"] = 0
            if vals:
                product.write(vals)
        return product_count

    @api.model
    def _get_ctx_vendor_price_case(self):
        return {"force_company": 1, "from_vendor_price": True}

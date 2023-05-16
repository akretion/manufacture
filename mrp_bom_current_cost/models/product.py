import logging

from odoo import api, fields, models

logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _set_current_costs_on_bom(self):
        templates = self.filtered(
            lambda t: t.product_variant_count == 1 and t.bom_count > 0
        )
        if templates:
            return templates.mapped("product_variant_id")._set_current_costs_on_bom()


class ProductProduct(models.Model):
    _inherit = "product.product"

    current_cost = fields.Float(
        groups="mrp.group_mrp_user",
        readonly=True,
        tracking=True,
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
    price_warn_conf = fields.Char(
        string="W",
        groups="mrp.group_mrp_user",
        help="Wrong configuration for current cost, see current tab",
    )

    def _check_current_price(self):
        """Check misconfigured bought products"""
        # TODO : make configurable by company
        # TODO optimize perf
        self.env["product.product"].search([]).write({"price_warn_conf": ""})
        for rec in self:
            sellers = rec.seller_ids.filtered(
                lambda s: not s.company_id or s.company_id.id == 1
            )
            if not sellers:
                rec.price_warn_conf = "⚠"

    def _compute_price_info(self):
        for rec in self:
            info = ""
            if rec.vendor_price_id:
                vals = {
                    "vendor": rec.vendor_price_id.name.name,
                    "price": rec.vendor_price_id.price,
                    "min_qty": rec.vendor_price_id.price,
                }
                info = "%(vendor)s\nPrice: %(price)s\nMin. qty: %(min_qty)s" % vals
            rec.vendor_price_info = info

    def _set_current_costs_on_bom(self):
        for product in self:
            bom = self.env["mrp.bom"]._bom_find(product=product)
            if bom:
                bom.product_tmpl_id.product_variant_ids[
                    0
                ].current_cost = bom._set_bom_lines_current_cost()

    def _set_current_cost(self):
        product_count = 0
        for product in self:
            quantity = 0
            if product.seller_ids:
                # if quantity is not provided seller_ids with quantities
                # can't be selected : fixed in v15 (testing if qty is none)
                # here is a minimal behavior
                quantity = product.seller_ids[0].min_qty or 1
            # You may change vendor_info selection
            # overiding _select_seller() according to the context
            vendor_info = product.with_context(
                self._get_ctx_vendor_price_case()
            )._select_seller(uom_id=product.uom_id, quantity=quantity)
            vals = {}
            if vendor_info:
                if vendor_info.price != product.current_cost:
                    vals["previous_cost"] = product.current_cost
                    vals["current_cost"] = vendor_info.price
                    vals["last_cost"] = fields.Date.today()
                    product_count += 1
                if vendor_info != product.vendor_price_id:
                    vals["vendor_price_id"] = vendor_info.id
            elif product.vendor_price_id:
                vals["vendor_price_id"] = False
                vals["current_cost"] = 0
            if vals:
                product.write(vals)
        return product_count

    @api.model
    def _get_ctx_vendor_price_case(self):
        return {"force_company": 1, "from_vendor_price": True}

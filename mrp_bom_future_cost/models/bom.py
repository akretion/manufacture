# © 2022 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import _, api, fields, models

logger = logging.getLogger(__name__)


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    future_cost = fields.Float(
        compute="_compute_future_cost",
        groups="mrp.group_mrp_user",
        help="Same field as in product (if only 1 variant)",
    )

    def _compute_future_cost(self):
        for rec in self:
            if rec.product_id:
                rec.future_cost = rec.product_id.future_cost
            elif len(rec.product_tmpl_id.product_variant_ids) == 1:
                rec.future_cost = rec.product_tmpl_id.product_variant_ids[
                    0
                ].future_cost
            else:
                rec.future_cost = 0

    @api.model
    def _computed_cost_with_vendor_price(self, default_company_id):
        """This method is periodically with a cron
        You may inherit to change the default company"""
        products = self.env["product.product"].search(
            self._get_domain_to_guess_products_to_purchase(default_company_id)
        )
        product_count = products.set_vendor_price()
        if product_count:
            partner = self._get_warned_partner_about_cost_with_vendor_price()
            partner.message_post(
                body=_("%s products price_vendor updated.") % product_count
            )
        product_tmpl = self.env["mrp.bom"].search([]).mapped("product_tmpl_id")
        product_tmpl.action_bom_vendor_price()

    @api.model
    def _get_warned_partner_about_cost_with_vendor_price(self):
        return self.env.ref("base.user_admin").partner_id

    @api.model
    def _get_domain_to_guess_products_to_purchase(self, company_id):
        buy_rte = self.env.ref(
            "purchase_stock.route_warehouse0_buy", raise_if_not_found=False
        )
        if buy_rte:
            # need to have purchase module installed
            return [
                ("route_ids", "=", buy_rte.id),
                "|",
                ("company_id", "=", company_id),
                ("company_id", "=", False),
            ]
        else:
            logger.info(
                "Impossible to guess if the product can be purchased. "
                "Please install purchase module or override "
                "_get_domain_to_guess_products_to_purchase() method."
            )
            return []

    def _compute_cost_with_vendor_price(self):
        """ """
        # duplicate from Product._compute_bom_price()
        self.ensure_one()
        total = 0
        for opt in self.routing_id.operation_ids:
            duration_expected = (
                opt.workcenter_id.time_start
                + opt.workcenter_id.time_stop
                + opt.time_cycle
            )
            total += (duration_expected / 60) * opt.workcenter_id.costs_hour
        # END duplicate
        for line in self.bom_line_ids:
            if line._skip_bom_line(self):
                continue
            # Compute recursive if line has `child_line_ids`
            if line.child_bom_id:
                child_cost = line.child_bom_id._compute_cost_with_vendor_price()
                if child_cost != line.product_id.future_cost:
                    line.product_id.previous_cost = line.product_id.future_cost
                    line.product_id.future_cost = child_cost
                    line.product_id.last_cost = fields.Date.today()
                total += (
                    line.product_id.uom_id._compute_price(
                        child_cost, line.product_uom_id
                    )
                    * line.product_qty
                )
            else:
                price = (
                    line.product_id.future_cost
                    or line.product_id.with_context(force_company=1).standard_price
                )
                total += (
                    line.product_id.uom_id._compute_price(price, line.product_uom_id)
                    * line.product_qty
                )
        return self.product_uom_id._compute_price(
            total / self.product_qty, self.product_tmpl_id.uom_id
        )


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    future_cost = fields.Float(
        related="product_id.future_cost",
        groups="mrp.group_mrp_user",
        help="Cost if matching vendor price in product page",
    )
    standard_price = fields.Float(
        compute="_compute_std_price",
        groups="mrp.group_mrp_user",
        help="The same as cost in product page",
    )

    def _compute_std_price(self):
        for rec in self:
            rec.standard_price = rec.product_id.with_context(
                force_company=1
            ).standard_price

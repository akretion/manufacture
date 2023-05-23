# © 2022 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import _, api, fields, models

logger = logging.getLogger(__name__)

"""
    Module Algorithm

    _compute_current_costs()    # called by cron              [mrp.bom]
        purchased_products._set_current_cost()                [product.product]
        manufactured_products._set_current_costs_on_bom()     [product.product]
            bom._set_bom_lines_current_cost()                 [mrp.bom]
"""


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    unit_current_cost = fields.Float(
        string="Unit Current Cost",
        compute="_compute_unit_current_cost",
        groups="mrp.group_mrp_user",
        tracking=True,
        help="Same field as in product (if only 1 variant) with quantity set to 1",
    )
    current_cost = fields.Float(
        string="Global Current Cost",
        compute="_compute_global_current_cost",
        groups="mrp.group_mrp_user",
        tracking=True,
        help="Same field as in product (if only 1 variant) with quantity set to 1",
    )
    currency_id = fields.Many2one(related="company_id.currency_id")

    def _compute_unit_current_cost(self):
        for rec in self:
            if rec.product_id:
                rec.unit_current_cost = rec.product_id.current_cost
            elif len(rec.product_tmpl_id.product_variant_ids) == 1:
                rec.unit_current_cost = rec.product_tmpl_id.product_variant_ids[
                    0
                ].current_cost
            else:
                rec.unit_current_cost = 0

    def _compute_global_current_cost(self):
        for rec in self:
            rec.current_cost = rec.unit_current_cost * rec.product_qty

    @api.model
    def _compute_current_costs(self, default_company_id):
        """This method is periodically with a cron
        You may inherit to change the default company"""
        self.env["product.product"].search([]).write({"price_warn_conf": ""})
        products = self._get_purchasable_products(default_company_id)
        product_count = products._set_current_cost()
        products._check_current_price()
        if product_count:
            partner = self._get_warned_partner_about_cost_with_vendor_price()
            partner.message_post(
                body=_("%s products price_vendor updated.") % product_count
            )
        product_tmpl = self.env["mrp.bom"].search([]).mapped("product_tmpl_id")
        product_tmpl._set_current_costs_on_bom()

    @api.model
    def _get_warned_partner_about_cost_with_vendor_price(self):
        return self.env.ref("base.user_admin").partner_id

    @api.model
    def _get_purchasable_products(self, company_id):
        "Search products which are not in mrp.bom"
        all_visible_products = self.env["product.product"].search(
            [
                ("escape_price_warn", "=", False),
                ("purchase_ok", "=", True),
                "|",
                ("company_id", "=", company_id),
                ("company_id", "=", False),
            ]
        )
        products_map = {x.product_tmpl_id: x for x in all_visible_products}
        boms = self.env["mrp.bom"].search(
            [
                (
                    "product_tmpl_id",
                    "in",
                    all_visible_products.mapped("product_tmpl_id").ids,
                )
            ]
        )
        not_raw_mat_ids = [
            x.product_id.id or products_map.get(x.product_tmpl_id)["id"] or 0
            for x in boms
        ]
        not_raw_mat_ids = list(set(not_raw_mat_ids))
        not_raw_mat_ids.sort()
        purchasable = all_visible_products - self.env["product.product"].browse(
            not_raw_mat_ids
        )
        return purchasable

    def _set_bom_lines_current_cost(self):
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
                child_cost = line.child_bom_id._set_bom_lines_current_cost()
                if child_cost != line.product_id.current_cost:
                    line.product_id.previous_cost = line.product_id.current_cost
                    line.product_id.current_cost = child_cost
                    line.product_id.last_cost = fields.Date.today()
                total += (
                    line.product_id.uom_id._compute_price(
                        child_cost, line.product_uom_id
                    )
                    * line.product_qty
                )
            else:
                price = (
                    line.product_id.current_cost
                    or line.product_id.with_context(force_company=1).standard_price
                )
                total += (
                    line.product_id.uom_id._compute_price(price, line.product_uom_id)
                    * line.product_qty
                )
        mo_price = self.product_uom_id._compute_price(
            total / self.product_qty, self.product_tmpl_id.uom_id
        )
        return mo_price


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    current_cost = fields.Float(
        related="product_id.current_cost",
        groups="mrp.group_mrp_user",
        help="Cost if matching vendor price in product page",
    )
    subtotal_current_cost = fields.Float(
        groups="mrp.group_mrp_user",
        compute="_compute_current_cost",
        help="Cost if matching vendor price in product page",
    )
    standard_price = fields.Float(
        string="Cost",
        compute="_compute_std_price",
        groups="mrp.group_mrp_user",
        help="The same as cost in product page",
    )
    currency_id = fields.Many2one(related="bom_id.company_id.currency_id")

    def _compute_current_cost(self):
        for rec in self:
            rec.subtotal_current_cost = rec.current_cost * rec.product_qty

    def _compute_std_price(self):
        for rec in self:
            rec.standard_price = rec.product_id.with_context(
                force_company=1
            ).standard_price

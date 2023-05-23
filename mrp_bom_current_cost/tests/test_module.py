# from odoo.exceptions import UserError
from odoo import tests, fields
from .helper import TestHelper


# class Test(tests.common.SavepointCase, TestHelper):
class Test(tests.common.TransactionCase, TestHelper):
    def setUp(self):
        super().setUp()
        # TODO test with a diff unit between product and bom line
        self._set_product("PF10", route="mrp.route_warehouse0_manufacture")
        self._set_product("PF20", route="mrp.route_warehouse0_manufacture")
        self._set_product("SE10", route="mrp.route_warehouse0_manufacture")
        self._set_product("SE20", route="mrp.route_warehouse0_manufacture")
        self._set_product("MP1", route="purchase_stock.route_warehouse0_buy")
        self._set_product("MP2", route="purchase_stock.route_warehouse0_buy")
        self._set_product("MP3", cost=41, route="purchase_stock.route_warehouse0_buy")
        self._set_sup_info("MP1_sup", "MP1", price=15)
        self._set_sup_info("MP2_sup", "MP2", price=24)
        bom_vals = {
            "product_tmpl_id": self.env.ref("any.pf10").product_tmpl_id.id,
        }
        self.create_or_update("mrp.bom", "pf10bom", bom_vals)
        bom_vals = {
            "product_tmpl_id": self.env.ref("any.pf20").product_tmpl_id.id,
        }
        self.create_or_update("mrp.bom", "pf20bom", bom_vals)
        bom_line_vals = {
            "bom_id": self.env.ref("any.pf10bom").id,
            "product_id": self.env.ref("any.se10").id,
            "product_qty": 1,
        }
        self.create_or_update("mrp.bom.line", "se10_pf10", bom_line_vals)
        bom_line_vals = {
            "bom_id": self.env.ref("any.pf10bom").id,
            "product_id": self.env.ref("any.mp2").id,
            "product_qty": 2,
        }
        self.create_or_update("mrp.bom.line", "mp2_pf10", bom_line_vals)
        bom_vals = {
            "product_tmpl_id": self.env.ref("any.se10").product_tmpl_id.id,
        }
        self.create_or_update("mrp.bom", "se10bom", bom_vals)
        bom_line_vals = {
            "bom_id": self.env.ref("any.se10bom").id,
            "product_id": self.env.ref("any.mp2").id,
            "product_qty": 2,
        }
        self.create_or_update("mrp.bom.line", "mp2_se10", bom_line_vals)
        bom_line_vals = {
            "bom_id": self.env.ref("any.se10bom").id,
            "product_id": self.env.ref("any.mp1").id,
            "product_qty": 3,
        }
        self.create_or_update("mrp.bom.line", "mp1_se10", bom_line_vals)
        bom_line_vals = {
            "bom_id": self.env.ref("any.pf20bom").id,
            "product_id": self.env.ref("any.mp2").id,
            "product_qty": 2,
        }
        self.create_or_update("mrp.bom.line", "mp2_pf20", bom_line_vals)
        bom_line_vals = {
            "bom_id": self.env.ref("any.pf20bom").id,
            "product_id": self.env.ref("any.mp3").id,
            "product_qty": 1,
        }
        self.create_or_update("mrp.bom.line", "mp3_pf20", bom_line_vals)
        self.env["mrp.bom"]._compute_current_costs(1)
        # Use `self.env.cr.commit()` here to create these data as demo

    def test_any(self):
        def ref(idstring, module="any"):
            return self.env.ref("%s.%s" % (module, idstring))

        assert ref("mp1").current_cost == ref("mp1").seller_ids[0].price
        assert ref("se10bom").unit_current_cost == 93
        assert ref("mp1").with_context(company_id=1).standard_price == 0

    def _set_product(self, code, name=None, cost=None, route=None):
        vals = {
            "name": "%s %s" % (name or code, "DEMO"),
            "type": "product",
            "standard_price": cost or 0,
            "default_code": code,
            "company_id": 1,
        }
        if route:
            vals["route_ids"] = [(4, self.env.ref(route).id, 0)]
        return self.create_or_update("product.product", code, vals)

    def _set_sup_info(self, xml_id, product_xml_id, price):
        xml_id = xml_id.lower()
        product = self.env.ref("any.%s" % product_xml_id.lower())
        vals = {
            "name": self.env.ref("base.res_partner_3").id,
            "price": price,
            "product_tmpl_id": product.product_tmpl_id.id,
        }
        self.create_or_update("product.supplierinfo", xml_id, vals)

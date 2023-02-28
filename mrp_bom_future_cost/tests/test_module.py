# from odoo.exceptions import UserError
from odoo import tests, fields
from .helper import TestHelper


class Test(tests.common.TransactionCase, TestHelper):
    def _set_product(self, code, name=None, cost=None):
        vals = {
            "name": "%s %s" % (name or code, "DEMO"),
            "type": "product",
            "standard_price": cost or 0,
            "default_code": code,
            "company_id": 1,
        }
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

    def setUp(self):
        super().setUp()
        self._set_product("PF10")
        self._set_product("PF20")
        self._set_product("SE10")
        self._set_product("SE20")
        self._set_product("MP1")
        self._set_product("MP2")
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
        self.env.cr.commit()

    def test_any(self):
        assert self.env.ref("any.mp1").with_context(company_id=1).standard_price == 0
        self.env.ref("any.mp1").with_context(company_id=1).standard_price = 4
        # This is the method triggrered by cron
        self.env["mrp.bom"]._computed_cost_with_vendor_price(1)
        assert self.env.ref("any.mp1").future_cost == 15
        assert self.env.ref("any.mp1").last_cost == fields.Date.today()
        assert self.env.ref("any.mp2").future_cost == 24

    # def setUpAny(self):
    #     super().setUpAny()

    #     # # Mainly copied from mrp_bom_cost
    #     # Products.
    #     self.dining_table = self._create_product("Dining Table", 1000)
    #     self.table_head = self._create_product("Table Head", 300)
    #     self.screw = self._create_product("Screw", 10)
    #     self.leg = self._create_product("Leg", 25)
    #     self.glass = self._create_product("Glass", 100)

    #     # Unit of Measure.
    #     self.unit = self.env.ref("uom.product_uom_unit")
    #     self.dozen = self.env.ref("uom.product_uom_dozen")

    #     # Bills Of Materials.
    #     # -------------------------------------------------------------------------------
    #     # Cost of BoM (Dining Table 1 Unit)
    #     # Component Cost =  Table Head   1 Unit * 300 = 300 (468.75 from it's components)
    #     #                   Screw        5 Unit *  10 =  50
    #     #                   Leg          4 Unit *  25 = 100
    #     #                   Glass        1 Unit * 100 = 100
    #     # Total = 550 [718.75 if components of Table Head considered] (for 1 Unit)
    #     # -------------------------------------------------------------------------------

    #     bom_form = tests.Form(self.env["mrp.bom"])
    #     bom_form.product_id = self.dining_table
    #     bom_form.product_tmpl_id = self.dining_table.product_tmpl_id
    #     bom_form.product_qty = 1.0
    #     bom_form.product_uom_id = self.unit
    #     bom_form.type = "normal"
    #     with bom_form.bom_line_ids.new() as line:
    #         line.product_id = self.table_head
    #         line.product_qty = 1
    #     with bom_form.bom_line_ids.new() as line:
    #         line.product_id = self.screw
    #         line.product_qty = 5
    #     with bom_form.bom_line_ids.new() as line:
    #         line.product_id = self.leg
    #         line.product_qty = 4
    #     with bom_form.bom_line_ids.new() as line:
    #         line.product_id = self.glass
    #         line.product_qty = 1
    #     bom_form.save()

    #     self._create_sup_info("screw", 17)
    #     self.screw.set_vendor_price()

    # def test_vendor_price_method(self):
    #     self.assertEqual(self.screw.future_cost, 17)

    # def test_on_final_product(self):
    #     self.dining_table.action_bom_vendor_price()
    #     self.assertEqual(self.dining_table.future_cost, 585)

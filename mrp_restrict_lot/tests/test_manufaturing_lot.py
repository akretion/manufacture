# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase

from odoo.addons.stock.models.stock_rule import StockRule


class TestRestrictLot(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer_loc = cls.env.ref("stock.stock_location_customers")
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.panel_wood_prd = cls.env.ref("mrp.product_product_wood_panel")
        manufacture_route = cls.env.ref("mrp.route_warehouse0_manufacture")
        mto_route = cls.env.ref("stock.route_warehouse0_mto")
        mto_route.write({"active": True})
        # ensure full make to order and not mts or mto
        mto_route.rule_ids.write({"procure_method": "make_to_order"})
        cls.panel_wood_prd.write(
            {"route_ids": [(4, manufacture_route.id, 0), (4, mto_route.id, 0)]}
        )
        cls.out_picking_type = cls.env.ref("stock.picking_type_out")

    def test_manufacturing_lot(self):
        lot = self.env["stock.lot"].create(
            {
                "name": "lot1",
                "product_id": self.panel_wood_prd.id,
                "company_id": self.warehouse.company_id.id,
            }
        )
        lot2 = self.env["stock.lot"].create(
            {
                "name": "lot2",
                "product_id": self.panel_wood_prd.id,
                "company_id": self.warehouse.company_id.id,
            }
        )

        move1 = self.env["stock.move"].create(
            {
                "product_id": self.panel_wood_prd.id,
                "location_id": self.warehouse.lot_stock_id.id,
                "location_dest_id": self.customer_loc.id,
                "product_uom_qty": 1,
                "product_uom": self.panel_wood_prd.uom_id.id,
                "procure_method": "make_to_order",
                "warehouse_id": self.warehouse.id,
                "restrict_lot_id": lot.id,
                "picking_type_id": self.out_picking_type.id,
            }
        )
        move1._action_confirm()
        mo1 = move1.move_orig_ids.production_id
        self.assertIn(lot, mo1.lot_producing_ids)
        self.assertEqual(mo1.name, lot.name)

        # second move for a different lot creates a separate MO
        move2 = self.env["stock.move"].create(
            {
                "product_id": self.panel_wood_prd.id,
                "location_id": self.warehouse.lot_stock_id.id,
                "location_dest_id": self.customer_loc.id,
                "product_uom_qty": 1,
                "product_uom": self.panel_wood_prd.uom_id.id,
                "procure_method": "make_to_order",
                "warehouse_id": self.warehouse.id,
                "restrict_lot_id": lot2.id,
                "picking_type_id": self.out_picking_type.id,
            }
        )
        move2._action_confirm()
        mo2 = move2.move_orig_ids.production_id
        self.assertEqual(mo2.name, lot2.name)
        self.assertEqual(
            mo2.move_finished_ids.restrict_lot_id,
            lot2,
            "ensure propagation of the restricted lot to the finished move",
        )

        mo2.button_mark_done()
        self.assertEqual(mo2.state, "done")
        self.assertIn(lot2, mo2.lot_producing_ids)
        self.assertEqual(
            mo2.move_finished_ids.restrict_lot_id,
            lot2,
            "ensure propagation of the restricted lot to the finished move after prod",
        )

        # change lot on MO 1 and ensure it's propagated
        mo1.lot_producing_ids = lot2
        mo1.button_mark_done()
        self.assertEqual(mo1.state, "done")
        self.assertIn(
            lot2,
            mo1.lot_producing_ids,
            "lot_producing_ids should propagate to move line",
        )
        self.assertEqual(
            mo1.move_finished_ids.restrict_lot_id,
            lot2,
            "ensure propagation of the restricted lot to the finished move after prod",
        )

    def test_dont_mix_manufacturing_lot(self):
        # in v19, each procurement creates its own MO (no merging via reference_ids).
        # ensure different lots produce different MOs and lot_producing_ids is set.
        lot1 = self.env["stock.lot"].create(
            {
                "name": "lot1",
                "product_id": self.panel_wood_prd.id,
                "company_id": self.warehouse.company_id.id,
            }
        )
        lot2 = self.env["stock.lot"].create(
            {
                "name": "lot2",
                "product_id": self.panel_wood_prd.id,
                "company_id": self.warehouse.company_id.id,
            }
        )

        group1 = StockRule.Procurement(
            self.panel_wood_prd,
            4,
            self.panel_wood_prd.uom_id,
            self.warehouse.lot_stock_id,
            "name",
            "origin",
            self.warehouse.company_id,
            {"restrict_lot_id": lot1.id},
        )
        group2 = StockRule.Procurement(
            self.panel_wood_prd,
            4,
            self.panel_wood_prd.uom_id,
            self.warehouse.lot_stock_id,
            "name",
            "origin",
            self.warehouse.company_id,
            {"restrict_lot_id": lot2.id},
        )
        group3 = StockRule.Procurement(
            self.panel_wood_prd,
            4,
            self.panel_wood_prd.uom_id,
            self.warehouse.lot_stock_id,
            "name",
            "origin",
            self.warehouse.company_id,
            {"restrict_lot_id": lot1.id},
        )

        # create first MO (lot1)
        self.env["stock.rule"].run([group1])
        mo1 = self.env["mrp.production"].search(
            [("lot_producing_ids", "in", [lot1.id])], limit=1
        )
        self.assertTrue(mo1, "MO for lot1 should be created")
        self.assertIn(lot1, mo1.lot_producing_ids)

        # create second MO (lot2) — must be a different MO
        self.env["stock.rule"].run([group2])
        mo2 = self.env["mrp.production"].search(
            [("lot_producing_ids", "in", [lot2.id])], limit=1
        )
        self.assertTrue(mo2, "MO for lot2 should be created")
        self.assertIn(lot2, mo2.lot_producing_ids)
        self.assertNotEqual(mo1.id, mo2.id, "Different lots must not share the same MO")

        # run a third procurement for lot1 — creates a separate MO in v19
        self.env["stock.rule"].run([group3])
        mo3 = self.env["mrp.production"].search(
            [("lot_producing_ids", "in", [lot1.id])], order="id desc", limit=1
        )
        self.assertIn(lot1, mo3.lot_producing_ids)
        self.assertNotEqual(mo3.id, mo2.id, "lot1 MO must not be confused with lot2 MO")

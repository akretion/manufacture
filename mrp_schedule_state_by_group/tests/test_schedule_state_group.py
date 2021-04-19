# © 2020 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo.addons.mrp.tests.common import TestMrpCommon


class TestSchedule(TestMrpCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        manuf_route = cls.env.ref("mrp.route_warehouse0_manufacture")
        mto_route = cls.env.ref("stock.route_warehouse0_mto")
        # make rulles full MTO
        mto_route.rule_ids.write({"procure_method": "make_to_order"})
        # use bom_1 from mrp test common
        cls.product_4.write({"route_ids": [(6, 0, [manuf_route.id, mto_route.id])]})

        # Create expedition with multiple moves MTO with manufactue product in order
        # to create a groupe of multiple MO for a same partner/destination (typlically
        # it would be a same sale order but this module does not need to depend on sale)
        cls.delivery_group = cls.env["procurement.group"].create({"name": "delivery 1"})
        delivery_type = cls.env.ref("stock.picking_type_out")
        customer_loc = cls.env.ref("stock.stock_location_customers")
        cls.move1 = cls.env["stock.move"].create(
            {
                "name": "test move 1",
                "product_id": cls.product_4.id,
                "product_uom": cls.product_4.uom_id.id,
                "product_uom_qty": 2,
                "location_id": delivery_type.default_location_src_id.id,
                "location_dest_id": customer_loc.id,
                "procure_method": "make_to_order",
                "origin": "Test 1",
                "warehouse_id": delivery_type.warehouse_id.id,
                "picking_type_id": delivery_type.id,
                "group_id": cls.delivery_group.id,
            }
        )
        cls.move1._action_confirm()
        cls.move2 = cls.env["stock.move"].create(
            {
                "name": "test move 1",
                "product_id": cls.product_4.id,
                "product_uom": cls.product_4.uom_id.id,
                "product_uom_qty": 1,
                "location_id": delivery_type.default_location_src_id.id,
                "location_dest_id": customer_loc.id,
                "procure_method": "make_to_order",
                "origin": "Test 1",
                "warehouse_id": delivery_type.warehouse_id.id,
                "picking_type_id": delivery_type.id,
                "group_id": cls.delivery_group.id,
            }
        )
        cls.move2._action_confirm(merge=False)

    def test_schedule_state_source_group(self):
        mo1 = self.move1.move_orig_ids.production_id
        mo2 = self.move2.move_orig_ids.production_id
        self.assertEqual(len(self.delivery_group.group_mo_ids), 2)
        location = mo1.location_src_id
        # put enough stock, product 1 is consu so only product 2
        inventory = self.env["stock.inventory"].create(
            {
                "name": "Test inventory",
                "location_ids": [(6, 0, [location.id])],
                "state": "confirm",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_2.id,
                            "location_id": location.id,
                            "product_qty": 50,
                        },
                    ),
                ],
            }
        )
        inventory._action_done()
        mo1.action_assign()
        # mo1 is assigned but still waiting since mo2, has the same delivery group
        # and its raw materials are not available yet
        self.assertEqual(mo1.reservation_state, "assigned")
        self.assertEqual(mo1.schedule_state, "waiting")
        mo2.action_assign()
        self.assertEqual(mo1.schedule_state, "todo")
        self.assertEqual(mo2.schedule_state, "todo")

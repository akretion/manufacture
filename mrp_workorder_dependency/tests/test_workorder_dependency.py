# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestWorkorderDepency(TransactionCase):
    def test_workorder_dependency(self):
        operation1 = self.env.ref("mrp.mrp_routing_workcenter_4")
        operation2 = self.env.ref("mrp.mrp_routing_workcenter_3")
        operation3 = self.env.ref("mrp.mrp_routing_workcenter_1")
        bom = operation1.bom_id
        product = self.env.ref("product.product_product_27")
        operation3.dependency_ids = [(6, 0, [operation1.id, operation2.id])]
        mo = self.env["mrp.production"].create(
            {
                "product_id": product.id,
                "bom_id": bom.id,
                "product_qty": 1.0,
                "product_uom_id": product.uom_id.id,
            }
        )
        self.env["stock.move"].create(mo._get_moves_raw_values())
        self.env["stock.move"].create(mo._get_moves_finished_values())
        mo._create_workorder()
        mo.action_confirm()
        wo1 = mo.workorder_ids.filtered(lambda wo: wo.operation_id.id == operation1.id)
        wo2 = mo.workorder_ids.filtered(lambda wo: wo.operation_id.id == operation2.id)
        wo3 = mo.workorder_ids.filtered(lambda wo: wo.operation_id.id == operation3.id)

        self.assertEqual(wo1.state, "ready")
        self.assertEqual(wo2.state, "ready")
        self.assertEqual(wo3.state, "pending")

        wo1.button_start()
        wo1.button_finish()

        self.assertEqual(wo2.state, "ready")
        self.assertEqual(wo3.state, "pending")

        wo2.button_start()
        wo2.button_finish()
        self.assertEqual(wo3.state, "ready")

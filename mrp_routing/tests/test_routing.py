# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestRouting(TransactionCase):
    def test_routing(self):
        routing = self.env["mrp.routing"].create({"name": "test"})
        operation = self.env.ref("mrp.mrp_routing_workcenter_5")
        operation.write({"bom_id": False, "routing_id": routing.id})
        bom = self.env.ref("mrp.mrp_bom_manufacture")
        self.assertEqual(len(bom.operation_ids), 0)
        bom.write({"routing_id": routing.id})
        self.assertEqual(len(bom.operation_ids), 1)

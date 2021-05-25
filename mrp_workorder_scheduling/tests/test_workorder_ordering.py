# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import exceptions
from odoo.tests.common import TransactionCase


class WorkorderOrdering(TransactionCase):
    def test_workorder_ordering(self):
        mo = self.env.ref("mrp.mrp_production_3")
        mo2 = mo.copy()
        mo2.action_confirm()
        (mo | mo2).write({"schedule_state": "scheduled"})
        workcenter = self.env.ref("mrp.mrp_workcenter_3")
        wos = workcenter.pending_order_ids
        self.assertEqual(len(wos), 2)

        with self.assertRaises(exceptions.UserError):
            workcenter.button_order_workorder()
        workcenter.write(
            {
                "ordering_key_id": self.env.ref(
                    "mrp_workorder_scheduling.create_date_ordering_key"
                )
            }
        )
        workcenter.button_order_workorder()
        ordered_wos = workcenter.pending_order_ids
        self.assertEqual(ordered_wos[0].production_id.id, mo.id)

        orderkey_create_date = self.env.ref("mrp_workorder_scheduling.ordering_field_1")
        # will order by id desc first
        orderkey_create_date.write({"sequence": 5})
        # else the order of ordering keys won't change since already in cache
        orderkey_create_date.invalidate_cache()
        workcenter.button_order_workorder()
        ordered_wos = workcenter.pending_order_ids
        self.assertEqual(ordered_wos[0].production_id.id, mo2.id)

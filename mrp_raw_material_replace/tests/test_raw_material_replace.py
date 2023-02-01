# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestMrpAvailability(TransactionCase):
    def setUp(self):
        super().setUp()
        self.sale1 = self.env.ref("base_custom.sale_order_1")
        self.raw_material_1 = self.env.ref("base_custom.raw_materiel_1_meters_bar")
        self.raw_material_3 = self.env.ref("base_custom.raw_material_3_unit_chariot")
        self.sale1.action_confirm()
        moves = self.sale1.procurement_group_id.stock_move_ids
        self.mo = moves.created_production_id.procurement_group_id.mrp_production_ids

    def test_raw_material_replacement(self):
        product_chariot_2 = self.env.ref("base_custom.raw_material_4_unit_chariot_2")
        wizard_obj = self.env["raw.material.swap"].with_context(active_ids=self.mo.ids)
        wizard = wizard_obj.create(
            {
                "product_id": self.raw_material_1.id,
                "product_replacement_id": product_chariot_2.id,
            }
        )
        # wrong UOM between products
        with self.assertRaises(UserError) as err:
            wizard.switch_product()
        expected_error = (
            "The unit of measure of the replcement component is not the "
            "same as the component to replace. Please chose a component "
            "with same unit of measure"
        )
        self.assertEqual(err.exception.name, expected_error)

        chariot_raw_move = self.mo.move_raw_ids.filtered(
            lambda move: move.product_id == self.raw_material_3
        )
        wizard.write({"product_id": self.raw_material_3.id})
        wizard.switch_product()
        self.assertEqual(chariot_raw_move.product_id, product_chariot_2)

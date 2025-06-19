# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestHardwarePlanLinkedProducts(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create products
        cls.raw_component = cls.env["product.product"].create(
            {"name": "Raw Component", "type": "consu"}
        )
        cls.semi_finished_product = cls.env["product.product"].create(
            {"name": "Semi-Finished Product", "type": "consu"}
        )
        cls.finished_product = cls.env["product.product"].create(
            {"name": "Finished Product", "type": "consu"}
        )
        cls.other_component = cls.env["product.product"].create(
            {"name": "Other Raw Component", "type": "consu"}
        )

        # Create BoMs for a 2-level hierarchy
        # Finished Product -> Semi-Finished Product -> Raw Component
        cls.bom_semi_finished = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.semi_finished_product.product_tmpl_id.id,
                "bom_line_ids": [
                    (0, 0, {"product_id": cls.raw_component.id, "product_qty": 1})
                ],
            }
        )
        cls.bom_finished = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.finished_product.product_tmpl_id.id,
                "bom_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.semi_finished_product.id,
                            "product_qty": 1,
                        },
                    )
                ],
            }
        )

        # Create a hardware plan linked to the raw component
        cls.plan_raw = cls.env["hardware.plan"].create(
            {
                "name": "Plan for Raw Component",
                "product_ids": [(6, 0, [cls.raw_component.id])],
            }
        )

    def test_00_initial_computation(self):
        """Test if linked products are computed correctly on creation."""
        # The recomputation is triggered on create, so linked_product_ids should be
        # populated
        expected_products = self.semi_finished_product | self.finished_product
        self.assertEqual(
            self.plan_raw.linked_product_ids.sorted(),
            expected_products.sorted(),
            "Initial computation should find all derivative products.",
        )

    def test_01_add_derivative_product(self):
        """Test adding a new derivative product at the top of the BoM chain."""
        # Create a new top-level product that uses the 'finished_product'
        top_product = self.env["product.product"].create({"name": "Top-Level Product"})
        self.env["mrp.bom"].create(
            {
                "product_tmpl_id": top_product.product_tmpl_id.id,
                "bom_line_ids": [
                    (0, 0, {"product_id": self.finished_product.id, "product_qty": 1})
                ],
            }
        )

        expected_products = (
            self.semi_finished_product | self.finished_product | top_product
        )
        self.assertEqual(
            self.plan_raw.linked_product_ids.sorted(),
            expected_products.sorted(),
            "Adding a new derivative BoM should update the linked products.",
        )

    def test_02_remove_bom_line(self):
        """Test removing a BoM line to break the chain."""
        # Remove the link between finished_product and semi_finished_product
        self.bom_finished.bom_line_ids.unlink()

        # finished_product should no longer be a derivative, but semi_finished should be
        self.assertEqual(
            self.plan_raw.linked_product_ids,
            self.semi_finished_product,
            "Removing a BoM line should update the linked products.",
        )

    def test_03_archive_bom(self):
        """Test the effect of archiving an intermediate BoM."""
        # Archive the BoM for the semi-finished product
        self.bom_semi_finished.action_archive()

        # The entire chain is broken, so no linked products should be found
        self.assertFalse(
            self.plan_raw.linked_product_ids,
            "Archiving an intermediate BoM should remove all subsequent derivatives.",
        )

    def test_04_unarchive_bom(self):
        """Test the effect of un-archiving an intermediate BoM."""
        # First, archive it
        self.bom_semi_finished.action_archive()
        self.assertFalse(
            self.plan_raw.linked_product_ids,
            "Sanity check: linked products should be empty after archive.",
        )

        # Then, unarchive it
        self.bom_semi_finished.action_unarchive()

        # The chain should be restored
        expected_products = self.semi_finished_product | self.finished_product
        self.assertEqual(
            self.plan_raw.linked_product_ids.sorted(),
            expected_products.sorted(),
            "Un-archiving a BoM should restore the linked products.",
        )

    def test_05_change_bom_line_product(self):
        """Test changing a component on a BoM line."""
        # Change the component of bom_semi_finished
        bom_line = self.bom_semi_finished.bom_line_ids
        bom_line.write({"product_id": self.other_component.id})

        # The chain from raw_component is now broken.
        self.assertFalse(
            self.plan_raw.linked_product_ids,
            "Changing a component should break the old derivative chain.",
        )

        # Optional: Check if a new plan for the new component would work
        plan_other = self.env["hardware.plan"].create(
            {
                "name": "Plan for Other Component",
                "product_ids": [(6, 0, [self.other_component.id])],
            }
        )
        expected_products = self.semi_finished_product | self.finished_product
        self.assertEqual(
            plan_other.linked_product_ids.sorted(),
            expected_products.sorted(),
            "The new component's plan should now see the derivatives.",
        )

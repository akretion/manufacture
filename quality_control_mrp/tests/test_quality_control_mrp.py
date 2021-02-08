# Copyright 2015 Oihane Crucelaegui - AvanzOSC
# Copyright 2018 Simone Rubino - Agile Business Group
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestQualityControlMrp(TransactionCase):

    def setUp(self):
        super(TestQualityControlMrp, self).setUp()
        self.production_model = self.env['mrp.production']
        self.inspection_model = self.env['qc.inspection']
        self.qc_trigger_model = self.env['qc.trigger']
        self.product = self.env.ref('mrp.product_product_wood_panel')
        self.test = self.env.ref('quality_control.qc_test_1')
        self.trigger = self.env.ref('quality_control_mrp.qc_trigger_mrp')
        self.bom = self.env['mrp.bom']._bom_find(product=self.product)
        self.production1 = self.production_model.create({
            'product_id': self.product.id,
            'product_qty': 2.0,
            'product_uom_id': self.product.uom_id.id,
            'bom_id': self.bom.id
        })
        self.production1.action_assign()
        inspection_lines = (
            self.inspection_model._prepare_inspection_lines(self.test))
        self.inspection1 = self.inspection_model.create({
            'name': 'Test Inspection',
            'inspection_lines': inspection_lines,
        })
        # Setup for manufacturing tracking product
        self.product2= self.env.ref('product.product_product_27')
        self.product2.qc_triggers = [(
            0, 0, {
                'trigger': self.trigger.id,
                'test': self.test.id,
            }
        )]
        self.lot_model = self.env['stock.production.lot']
        self.lot1 = self.lot_model.create(
            {"name": "000001", "product_id": self.product2.id}
        )
        self.lot2 = self.lot_model.create(
            {"name": "000002", "product_id": self.product2.id}
        )
        self.bom2 = self.env['mrp.bom']._bom_find(product=self.product2)
        self.production2 = self.production_model.create({
            'product_id': self.product2.id,
            'product_qty': 2.0,
            'product_uom_id': self.product2.uom_id.id,
            'bom_id': self.bom2.id
        })
        self.production2.action_assign()

    def _produce_production(self, production_id, qty, lot_ids=None):
        if lot_ids :
            for lot_id in lot_ids:
                produce_wizard = self.env['mrp.product.produce'].with_context({
                    'active_id': production_id.id,
                    'active_ids': [production_id.id],
                }).create({
                    'product_qty': qty,
                    'lot_id': lot_id.id,
                })
                produce_wizard.do_produce()
            production_id.post_inventory()
        else:
            produce_wizard = self.env['mrp.product.produce'].with_context({
                'active_id': production_id.id,
                'active_ids': [production_id.id],
            }).create({
                'product_qty': qty,
            })
            produce_wizard.do_produce()
            production_id.post_inventory()

    def test_inspection_create_for_product(self):
        self.product.qc_triggers = [(
            0, 0, {
                'trigger': self.trigger.id,
                'test': self.test.id,
            }
        )]
        self._produce_production(self.production1, self.production1.product_qty)
        self.assertEqual(self.production1.created_inspections, 1,
                         'Only one inspection must be created')

    def test_inspection_create_for_template(self):
        self.product.product_tmpl_id.qc_triggers = [(
            0, 0, {
                'trigger': self.trigger.id,
                'test': self.test.id,
            }
        )]
        self._produce_production(self.production1, self.production1.product_qty)
        self.assertEqual(self.production1.created_inspections, 1,
                         'Only one inspection must be created')

    def test_inspection_create_for_category(self):
        self.product.categ_id.qc_triggers = [(
            0, 0, {
                'trigger': self.trigger.id,
                'test': self.test.id,
            }
        )]
        self._produce_production(self.production1, self.production1.product_qty)
        self.assertEqual(self.production1.created_inspections, 1,
                         'Only one inspection must be created')

    def test_inspection_create_only_one(self):
        self.product.qc_triggers = [(
            0, 0, {
                'trigger': self.trigger.id,
                'test': self.test.id,
            }
        )]
        self.product.categ_id.qc_triggers = [(
            0, 0, {
                'trigger': self.trigger.id,
                'test': self.test.id,
            }
        )]
        self._produce_production(self.production1, self.production1.product_qty)
        self.assertEqual(self.production1.created_inspections, 1,
                         'Only one inspection must be created')

    def test_inspection_with_partial_fabrication(self):
        self.product.qc_triggers = [(
            0, 0, {
                'trigger': self.trigger.id,
                'test': self.test.id,
            }
        )]

        self._produce_production(self.production1, 1)
        self.assertEqual(self.production1.created_inspections, 1,
                         'Only one inspection must be created.')

        self._produce_production(self.production1, 1)
        self.assertEqual(self.production1.created_inspections, 2,
                         'There must be only 2 inspections.')

    def test_qc_inspection_mo(self):
        self.inspection1.write({
            'object_id': '%s,%d' % (self.production1._name,
                                    self.production1.id),
        })
        self.assertEquals(self.inspection1.production_id,
                          self.production1)

    def test_inspection_with_product_tracking(self):
        self._produce_production(self.production2, 1, self.lot1 | self.lot2)

        self.assertEqual(self.production2.created_inspections, 2,
                         'There must be 2 inspections created.')
        self.assertEqual(self.production2.qc_inspections_ids[0].lot_id.id, self.lot1.id)
        self.assertEqual(self.production2.qc_inspections_ids[1].lot_id.id, self.lot2.id)

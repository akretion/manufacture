# Copyright 2018 ABF OSIELL <http://osiell.com>
# Copyright 2019 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    root_id = fields.Many2one(
        "mrp.production", "Root order", index=True, ondelete="restrict", readonly=True
    )
    parent_id = fields.Many2one(
        "mrp.production",
        "Parent order",
        index=True,
        ondelete="restrict",
        readonly=True,
    )
    child_ids = fields.One2many(
        "mrp.production",
        "parent_id",
        "Children orders",
        domain=[("state", "!=", "cancel")],
    )

    def _generate_moves(self):
        """Overloaded to pass the created production order ID in the context.
        It will be used by the 'stock_rule._prepare_mo_vals()' overload to
        set the parent relation between production orders.
        """
        for prod in self:
            # Set the initial root production order ID
            if not prod.env.context.get("root_mrp_production_id"):
                prod = prod.with_context(root_mrp_production_id=self.id)
            # Set the parent production order ID
            prod = prod.with_context(parent_mrp_production_id=self.id)
            super(MrpProduction, prod)._generate_moves()
        return True

    def open_production_tree(self):
        self.ensure_one()
        tree_view = self.env.ref("mrp_production_hierarchy.mrp_production_tree_view")
        form_view = self.env.ref("mrp_production_hierarchy.mrp_production_form_view")

        if self.child_ids:
            return {
                "domain": [("root_id", "=", self.id)],
                "name": _("Hierarchy"),
                "view_mode": "tree",
                "res_model": "mrp.production",
                "views": [(tree_view.id, "tree"), (form_view.id, "form")],
                "target": "current",
                "type": "ir.actions.act_window",
                "context": dict(
                    self.env.context,
                    search_default_group_by_root_id=True,
                    search_default_group_by_parent_id=True,
                ),
            }
        return False

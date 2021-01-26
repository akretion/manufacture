# Copyright 2018 ABF OSIELL <http://osiell.com>
# Copyright 2019 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def get_obj_url(self, id=None, model="mrp.production"):
        """Returns object's url to access a form from report"""
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        obj_id = str(id or self.id)
        return base_url + "/web#id=" + obj_id + "&model=" + model + "&view_type=form"

    def qty_strip(self, qty):
        """Used in report to strip unuseful zero in decimals"""
        return str(qty).rstrip("0").rstrip(".")

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
    hierarchy_level = fields.Integer(string="MO Hierarchy level", default=0)
    child_ids = fields.One2many(
        "mrp.production",
        "parent_id",
        "Children orders",
        domain=[("state", "!=", "cancel")],
    )

    all_move_raw_ids = fields.Many2many(
        string="All the active Root Order related moves",
        comodel_name="stock.move",
        compute="_compute_all_move_raw_ids",
        help="All the move_raw_ids from Root Order and its descendants (not cancelled) "
        "ordered by going to the hierachy tree extremity first (before going to "
        "the next sibling)",
    )

    css_class = fields.Char(
        string="CSS class",
        compute="_compute_css_class",
        help="Bootstrap CSS class used in hierarchy report to inform about the "
        "Manufacturing Order progress",
    )

    @api.depends("root_id", "child_ids")
    def _compute_all_move_raw_ids(self):
        for mo in self:
            root_id = mo.root_id or mo
            all_move_raw_ids = self.env["stock.move"]

            to_parse = root_id.move_raw_ids.filtered(lambda m: m.state != "cancel")
            while to_parse:
                all_move_raw_ids |= to_parse[0]

                parsed = to_parse[0]
                to_parse = to_parse[1:]
                if parsed.sub_production_id:
                    to_add = parsed.sub_production_id.move_raw_ids.filtered(
                        lambda m: m.state != "cancel"
                    )
                    to_parse = to_add | to_parse

            mo.all_move_raw_ids = all_move_raw_ids

    @api.depends("state", "check_to_done", "availability")
    def _compute_css_class(self):
        for mo in self:
            if mo.state == "done":
                mo.css_class = "text-muted"
            elif mo.check_to_done or mo.availability == "assigned":
                mo.css_class = "text-success"
            elif mo.state == "confirmed" and mo.availability in ("partially_available"):
                mo.css_class = "text-warning"
            else:
                mo.css_class = "text-danger"

    def _generate_moves(self):
        """Overloaded to pass the created production order ID in the context.
        It will be used by the 'stock_rule._prepare_mo_vals()' overload to
        set the parent relation between production orders.
        """
        for mo in self:
            # Set the initial root production order ID
            if not mo.env.context.get("root_mrp_production_id"):
                mo = mo.with_context(root_mrp_production_id=mo.id)
            # Set the parent production order ID
            mo = mo.with_context(parent_mrp_production_id=mo.id)
            super(MrpProduction, mo)._generate_moves()
        return True

    def open_order_hierarchy(self):
        self.ensure_one()
        # Compute all the latest moves related to all the orders
        self._compute_all_move_raw_ids()
        self.all_move_raw_ids._compute_delivery_picking_id()

        return self.env.ref(
            "mrp_production_hierarchy.action_report_production_hierarchy"
        ).report_action(self)

    def open_order_children(self):
        self.ensure_one()
        tree_view = self.env.ref("mrp_production_hierarchy.mrp_production_tree_view")
        form_view = self.env.ref("mrp_production_hierarchy.mrp_production_form_view")

        if self.child_ids:
            action = {
                "name": _("Hierarchy"),
                "view_mode": "tree",
                "res_model": "mrp.production",
                "views": [(tree_view.id, "tree"), (form_view.id, "form")],
                "target": "current",
                "type": "ir.actions.act_window",
            }
            if self.root_id:
                # Display all the (grand)children of an intermediary order
                action.update(
                    {
                        # We assume that all the (grand)children will have an id greater
                        # than the current intermediary order
                        "domain": [
                            ("root_id", "=", self.root_id.id),
                            ("id", ">", self.id),
                        ],
                        "context": dict(
                            self.env.context,
                            search_default_group_by_root_id=False,
                            search_default_group_by_parent_id=True,
                        ),
                    }
                )
            else:
                action.update(
                    {
                        "domain": [("root_id", "=", self.id)],
                        "context": dict(
                            self.env.context,
                            search_default_group_by_root_id=True,
                            search_default_group_by_parent_id=True,
                        ),
                    }
                )

            return action
        return False

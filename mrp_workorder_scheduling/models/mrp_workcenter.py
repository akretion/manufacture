# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, exceptions, fields, models


class MrpWorkcenter(models.Model):
    _inherit = "mrp.workcenter"

    ordering_key_id = fields.Many2one(
        "mrp.workcenter.ordering.key",
        string="Ordering Key",
        help="Allow to define Work Orders ordering priority",
    )

    def button_order_workorder(self):
        workorder_obj = self.env["mrp.workorder"]
        for workcenter in self:
            if not workcenter.ordering_key_id:
                raise exceptions.UserError(
                    _(
                        "The automatic ordering can not be processed as the "
                        'ordering key is empty. Please go in the tab "Ordering"'
                        ' and fill the field "ordering key"'
                    )
                )
            order_by = [
                "%s %s" % (row.field_id.name, row.order)
                for row in workcenter.ordering_key_id.field_ids
            ]
            workorders = workorder_obj.search(
                [
                    ("state", "in", ("pending", "ready", "progress")),
                    ("workcenter_id", "=", workcenter.id),
                    ("schedule_state", "=", "scheduled"),
                ],
                order=", ".join(order_by),
            )
            count = 1
            for prod_line in workorders:
                vals = {"sequence": count}
                count += 1
                prod_line.write(vals)
        return True

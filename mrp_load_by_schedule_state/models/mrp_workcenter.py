# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class MrpWorkcenter(models.Model):
    _inherit = "mrp.workcenter"

    qty_load = fields.Float(
        string="Total Load (qty)",
        compute="_compute_load",
        help="Load for this particular workcenter in quantity of pieces",
    )
    qty_waiting_load = fields.Float("Waiting (qty)", compute="_compute_load", store=True)
    qty_todo_load = fields.Float("Todo (qty)", compute="_compute_load", store=True)
    qty_scheduled_load = fields.Float("Scheduled (qty)", compute="_compute_load", store=True)
    waiting_load = fields.Float("Waiting (minutes)", compute="_compute_load", store=True)
    todo_load = fields.Float("Todo (minutes)", compute="_compute_load", store=True)
    scheduled_load = fields.Float("Scheduled (minutes)", compute="_compute_load", store=True)
    # Change its compute method to put the same to avoid calling the other method
    # as well when it already computes it for all other fields (performance)
    workcenter_load = fields.Float(compute="_compute_load", store=True)

    def _compute_load(self):
        res = self.env["mrp.workorder"].read_group(
            [
                ("workcenter_id", "in", self.ids),
                ("state", "in", ("pending", "ready", "progress")),
            ],
            ["workcenter_id", "schedule_state", "duration_expected", "qty_production"],
            ["workcenter_id", "schedule_state"],
            lazy=False,
        )
        result = {wid: {"qty": {}, "time": {}} for wid in self.ids}
        for res_group in res:
            result[res_group["workcenter_id"][0]]["time"][
                res_group["schedule_state"]
            ] = res_group["duration_expected"]
            result[res_group["workcenter_id"][0]]["qty"][
                res_group["schedule_state"]
            ] = res_group["qty_production"]
        for workcenter in self:
            workcenter.waiting_load = result[workcenter.id]["time"].get("waiting", 0.0)
            workcenter.qty_waiting_load = result[workcenter.id]["qty"].get(
                "waiting", 0.0
            )

            workcenter.todo_load = result[workcenter.id]["time"].get("todo", 0.0)
            workcenter.qty_todo_load = result[workcenter.id]["qty"].get("todo", 0.0)

            workcenter.scheduled_load = result[workcenter.id]["time"].get(
                "scheduled", 0.0
            )
            workcenter.qty_scheduled_load = result[workcenter.id]["qty"].get(
                "scheduled", 0.0
            )

            workcenter.qty_load = sum(
                qty for _schedule_state, qty in result[workcenter.id]["qty"].items()
            )
            workcenter.workcenter_load = sum(
                load for _schedule_state, load in result[workcenter.id]["time"].items()
            )

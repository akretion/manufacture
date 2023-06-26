# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class MrpWorkcenter(models.Model):
    _inherit = "mrp.workcenter"

    qty_load = fields.Float(
        string="Total Load (qty)",
        compute="_compute_load",
        store=True,
        help="Load for this particular workcenter in quantity of pieces",
    )
    qty_waiting_load = fields.Float(
        "Waiting (qty)", compute="_compute_load", store=True
    )
    qty_todo_load = fields.Float("Todo (qty)", compute="_compute_load", store=True)
    qty_scheduled_load = fields.Float(
        "Scheduled (qty)", compute="_compute_load", store=True
    )
    waiting_load = fields.Float(
        "Waiting (minutes)", compute="_compute_load", store=True
    )
    todo_load = fields.Float("Todo (minutes)", compute="_compute_load", store=True)
    scheduled_load = fields.Float(
        "Scheduled (minutes)", compute="_compute_load", store=True
    )
    # Change its compute method to put the same to avoid calling the other method
    # as well when it already computes it for all other fields (performance)
    workcenter_load = fields.Float(compute="_compute_load", store=True)

    # it is stored only because it is mandatory, in order to get the sum on the views
    # We used to compute when user click on the menu, but now it is cached and
    # overriding the load controller does not work.
    # I choose for now to compute it overriding the web_search_read/read_group
    # as it is really something needed only for the tree view.
    # maybe it would be better to put the right api.depends, but I fear it
    # recompute a lot and add a lot of conccurent update in widly used database.
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

    @api.model
    def web_read_group(
        self,
        domain,
        fields,
        groupby,
        limit=None,
        offset=0,
        orderby=False,
        lazy=True,
        expand=False,
        expand_limit=None,
        expand_orderby=False,
    ):
        self.search(domain, offset=offset, limit=limit, order=orderby)._compute_load()
        return super().web_read_group(
            domain,
            fields,
            groupby,
            limit=limit,
            offset=offset,
            orderby=orderby,
            lazy=lazy,
            expand=expand,
            expand_limit=expand_limit,
            expand_orderby=False,
        )

    @api.model
    def web_search_read(
        self,
        domain=None,
        fields=None,
        offset=0,
        limit=None,
        order=None,
        count_limit=None,
    ):
        search_domain = domain or []
        self.search(
            search_domain, offset=offset, limit=limit, order=order
        )._compute_load()
        return super().web_search_read(
            domain=domain,
            fields=fields,
            offset=offset,
            limit=limit,
            order=order,
            count_limit=count_limit,
        )

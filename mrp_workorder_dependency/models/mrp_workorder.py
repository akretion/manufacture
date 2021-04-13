# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, exceptions, fields, models


class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"

    def check_waiting_state(self):
        pendings = self.browse(False)
        not_pendings = self.browse(False)
        to_check = self.filtered(lambda wo: wo.state in ("pending", "ready"))
        for wo in to_check:
            for depend_line in wo.dependency_ids:
                if depend_line.state not in ("done", "cancel"):
                    if not wo.state == "pending":
                        pendings |= wo
                    break
            else:
                if wo.state == "pending":
                    not_pendings |= wo
        if pendings:
            pendings.write({"state": "pending"})
        if not_pendings:
            not_pendings.write({"state": "ready"})

    @api.depends("operation_id.dependency_ids")
    def _compute_dependency_ids(self):
        for line in self:
            ids = []
            if line.operation_id.dependency_ids:
                operation_ids = line.operation_id.dependency_ids.ids
                depend_lines = self.search(
                    [
                        ["production_id", "=", line.production_id.id],
                        ["operation_id", "in", operation_ids],
                    ]
                )
                ids = depend_lines.ids
            line.dependency_ids = [(6, 0, ids)]

    @api.depends("operation_id.dependency_for_ids")
    def _compute_dependency_for_ids(self):
        for line in self:
            ids = []
            if line.operation_id.dependency_for_ids:
                operation_ids = line.operation_id.dependency_for_ids.ids
                depend_lines = self.search(
                    [
                        ["production_id", "=", line.production_id.id],
                        ["operation_id", "in", operation_ids],
                    ]
                )
                ids = depend_lines.ids
            line.dependency_for_ids = [(6, 0, ids)]

    operation_id = fields.Many2one(index=True)
    dependency_ids = fields.Many2many(
        compute="_compute_dependency_ids",
        comodel_name="mrp.workorder",
        string="Dependency",
    )
    dependency_for_ids = fields.Many2many(
        compute="_compute_dependency_for_ids",
        comodel_name="mrp.workorder",
        string="Dependency for",
    )

    # totally override this method to manage multi dependencies
    def _start_nextworkorder(self):
        if self.state in ("done", "cancel") and self.dependency_for_ids:
            self.dependency_for_ids.filtered(
                lambda wo: wo.state == "pending"
            ).check_waiting_state()

    def write(self, vals):
        if vals.get("state") in ("done", "progress"):
            pending_wos = self.filtered(lambda wo: wo.state == "pending")
            if pending_wos:
                raise exceptions.UserError(
                    _(
                        "Impossible to start or end a workorder waiting for another one"
                        " (%s)" % pending_wos.ids
                    )
                )
        res = super().write(vals)
        if "operation_id" in vals:
            ops = self | self.mapped("dependency_for_ids")
            ops.check_waiting_state()
        return res

    def action_cancel(self):
        res = super().action_cancel()
        self._start_nextworkorder()
        return res

    # Default state is pending in Odoo and in _action_assign, the first (lower sequence)
    # is set to ready. But with this module multiple operations may not have
    # dependencies and should change to ready on _action_confirm
    def _action_confirm(self):
        res = super()._action_confirm()
        self.check_waiting_state()
        return res

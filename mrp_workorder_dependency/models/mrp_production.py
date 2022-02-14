# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def button_mark_done(self):
        # If we validate MOs directly without validating the workorders one by one
        # we don't want to have workorders dependencies issue since they will all be
        # done
        pending_wos = self.workorder_ids.filtered(lambda wo: wo.state == "pending")
        if pending_wos:
            pending_wos.write({"state": "ready"})
        return super().button_mark_done()

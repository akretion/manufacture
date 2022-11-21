from odoo import http
from odoo.http import request

from odoo.addons.web.controllers import action


class Action(action.Action):
    @http.route("/web/action/load", type="json", auth="user")
    def load(self, action_id, additional_context=None):
        if "mrp_load_by_schedule_state" in request.env.registry._init_modules:
            env = request.env
            try:
                action_id = int(action_id)
                mrp_action_id = env.ref("mrp.mrp_workcenter_action").id
                if action_id == mrp_action_id:
                    env["mrp.workcenter"].search([])._compute_load()
            except ValueError:
                if action_id == "mrp.mrp_workcenter_action":
                    env["mrp.workcenter"].search([])._compute_load()
        return super().load(action_id, additional_context=additional_context)

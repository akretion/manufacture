from odoo import api, tools, fields, models
from functools import lru_cache


class Inputline(models.Model):
    _name = "input.line"
    _description = "Line configuration scenari"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char()
    sequence = fields.Integer()
    bom_id = fields.Many2one(
        comodel_name="mrp.bom",
        required=True,
    )
    alert = fields.Html(
        help="Outside limit configuration is reported here",
        compute="_compute_alert",
        store=True,
    )
    satisfies_constraint = fields.Boolean(
        store=True,
        help="True if the input line satisfies the constraints",
    )
    constraint_suggestions = fields.Text()
    bom_data_preview = fields.Json()

    def _get_config_elements(self):
        """_get_config_elements must be overriden and return
        the specific fields in the input line"""

    def _input_line_values(self):
        elements = dict()
        for elm in self._get_config_elements():
            elements[elm] = self[elm]
        return elements

    @lru_cache
    def _cached_get_input_line_values(self):
        return self._input_line_values()

    def _clear_cache_input_line_values(self):
        return self._cached_get_input_line_values.cache_clear()

    def _get_input_line_values(self):
        if self.env.context.get("use_input_line_values_cache"):
            return self._cached_get_input_line_values()

        return self._input_line_values()

    def check_one_data(self):
        pass

    def open_form_pop_up(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Input line information",
            "res_model": "input.line",
            "view_mode": "form",
            "target": "new",
            "res_id": self.id,
        }

    def _check_constraint(self):
        self.ensure_one()
        return []

    @api.depends("bom_id")
    def _compute_alert(self):
        "You need to override this method in your custom config to trigger adhoc checks"

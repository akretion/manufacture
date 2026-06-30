from functools import lru_cache

from odoo import api, fields, models


MAIN_FIELDS = [
    "name",
    "sequence",
    "bom_id",
    "alert",
    "satisfies_constraint",
    "constraint_suggestions",
    "bom_data_preview",
]


class ProductConfig(models.Model):
    _name = "product.config"
    _description = "Line configuration scenari"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    # fields in this class (not inherited ones) must be declared in MAIN_FIELDS
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
        """Resulting fields are the specific ones dedicated to your own process"""
        fields_ = (
            self.env["ir.model.fields"]
            .search([("model", "=", "product.config")])
            .filtered(lambda s: s.ttype not in ("many2many", "one2many"))
            .mapped("name")
        )
        field_names = [
            x
            for x in fields_
            # create_date, write_uid, ...
            if x not in models.MAGIC_COLUMNS
            and x not in MAIN_FIELDS
            # these are chatter fields
            and not x.startswith("message_")
            # these are activity manager fields
            and not x.startswith("activity_")
            and x
            not in (
                "display_name",
                "has_message",
                "my_activity_date_deadline",
                "order_line_id",  # comes from sale_mrp_bom_configurable module
            )
        ]
        return field_names

    def _product_config_values(self):
        elements = dict()
        for elm in self._get_config_elements():
            elements[elm] = self[elm]
        return elements

    # We need to use a lru cache because this is called a lot and triggers
    # a lot of a read from the cache during mrp.production generation
    @lru_cache  # noqa: B019
    def _cached_get_product_config_values(self):
        return self._product_config_values()

    def _clear_cache_product_config_values(self):
        return self._cached_get_product_config_values.cache_clear()

    def _get_product_config_values(self):
        if self.env.context.get("use_product_config_values_cache"):
            return self._cached_get_product_config_values()

        return self._product_config_values()

    def check_one_data(self):
        pass

    def open_form_pop_up(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Input line information",
            "res_model": "product.config",
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

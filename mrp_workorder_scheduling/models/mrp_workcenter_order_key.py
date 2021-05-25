# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MrpWorkcenterOrderingKey(models.Model):
    _name = "mrp.workcenter.ordering.key"
    _description = "Workcenter Ordering Key"

    name = fields.Char("Name")
    field_ids = fields.One2many(
        "mrp.workcenter.ordering.field", "ordering_key_id", "Fields"
    )


class MrpWorkcenterOrderingField(models.Model):
    _name = "mrp.workcenter.ordering.field"
    _description = "Workcenter Ordering Field"
    _order = "sequence ASC"

    sequence = fields.Integer("Sequence")
    ordering_key_id = fields.Many2one("mrp.workcenter.ordering.key", "Workcenter")
    field_id = fields.Many2one(
        "ir.model.fields",
        string="Work Order Field",
        domain=[("model", "=", "mrp.workorder"), ("store", "=", True)],
    )
    ttype = fields.Selection(related="field_id.ttype", string="Type", readonly=True)
    order = fields.Selection(
        [("asc", "Asc"), ("desc", "Desc")], string="Order", default="asc"
    )

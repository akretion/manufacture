from odoo import fields, models


class InputConfig(models.Model):
    _name = "input.config"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Product configuration scenari"

    name = fields.Char(required=True)
    date = fields.Date(string="Date", default=fields.Date.today())
    bom_id = fields.Many2one(
        comodel_name="mrp.bom", string="Configurable Product", required=True
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("pending", "Pending"),
            ("confirmed", "Confirmed"),
        ],
        default="draft",
        ondelete={"pending": "draft", "confirmed": "draft"},
    )
    sale_id = fields.Many2one(comodel_name="sale.order")
    partner_id = fields.Many2one(
        comodel_name="res.partner", related="sale_id.partner_id.commercial_partner_id"
    )
    line_ids = fields.One2many(comodel_name="input.line", inverse_name="config_id")
    line_count = fields.Integer(string="Lines", compute="_compute_line_count")

    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec.line_ids)

    def show_lines(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Lines",
            "view_mode": "tree",
            "res_model": "input.line",
            "domain": [("config_id", "=", self.id)],
        }

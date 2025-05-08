# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    eco_id = fields.Many2one("engineering.change.order")
    previous_bom_id = fields.Many2one("mrp.bom")

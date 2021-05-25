# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"
    _order = "sequence"

    sequence = fields.Integer(index=True)

# -*- coding: utf-8 -*-
# © 2019 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class SwitchWorkcenter(models.TransientModel):
    _inherit = 'switch.workcenter'

    automatic_ordering = fields.Boolean(
        default=True)

    @api.multi
    def switch_workcenter(self):
        res = super(SwitchWorkcenter, self).switch_workcenter()
        if self.automatic_ordering:
            self.workcenter_id.button_order_workorder()
        return res

#  Copyright (C) 2021 Akretion (http://www.akretion.com).

from odoo import fields, models


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    group_mo_ids = fields.One2many(
        "mrp.production",
        "source_procurement_group_id",
        help="Technical field to gather all MOs belonging to the same source group."
        "Usually a same sale order or RMA for instance",
    )

    def _is_mo_plannable(self):
        self.ensure_one()
        plannable_group = all(
            [
                x.reservation_state == "assigned"
                for x in self.group_mo_ids.filtered(
                    lambda mo: mo.state not in ("done", "cancel", "draft")
                )
            ]
        )
        return plannable_group

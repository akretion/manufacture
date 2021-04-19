#  Copyright (C) 2015 Akretion (http://www.akretion.com).

from odoo import api, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    @api.depends(
        "reservation_state",
        "state",
        "source_procurement_group_id.group_mo_ids.state",
        "source_procurement_group_id.group_mo_ids.reservation_state",
    )
    def _compute_schedule_state(self):
        return super()._compute_schedule_state()

    def _get_mo_plannable(self):
        res = {}
        mo_with_group = self.filtered(lambda mo: mo.source_procurement_group_id)
        mo_without_group = self - mo_with_group
        for group in mo_with_group.mapped("source_procurement_group_id"):
            plannable_group = all(
                [x.reservation_state == "assigned" for x in group.group_mo_ids]
            )
            for mo in group.group_mo_ids:
                res[mo.id] = plannable_group
        no_group_plannable = super(MrpProduction, mo_without_group)._get_mo_plannable()
        res.update(no_group_plannable)
        return res

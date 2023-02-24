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

    @api.model_create_multi
    def create(self, vals_list):
        # TODO FIXME ugly patch for an ugly bug as we like it...
        # We need to fix this in an other manner ASAP. This is a hack and not good
        # for performance.
        # I don't fully understand the bug right now but does not have time to dig more

        # The fact taht we add a api.depends on "source_procurement_group_id"
        # (in _compute_schedule_state) make odoo want to compute workorder_ids
        # (not sure why exactly) at MO creation. Problem is that it then compute a lot
        # of stuff (state, then finished move ids and it create it but at this time
        # move_dest_ids is not set yet. So the finished move has no move_dest_ids
        # and it is an issue...

        # I choose to recompute the finished move as it seems not have the src
        # src procurement could have some impacts (at least it had on some custom
        # modules) maybe just recomputing finishing move for temporary missing
        # move_dest_ids is better.
        # let's see how it goes this way for now
        mos = super().create(vals_list)
        mos._compute_move_finished_ids()
        return mos

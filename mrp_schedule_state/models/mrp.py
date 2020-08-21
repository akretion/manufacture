#  Copyright (C) 2015 Akretion (http://www.akretion.com).
#  @author David BEAL <david.beal@akretion.com>

from openerp import models, api, fields, _
from openerp.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = ["mrp.production", "abstract.selection.rotate"]
    _name = "mrp.production"

    @api.model
    def _set_schedule_states(self):
        return [
            ("waiting", _("Waiting")),
            ("todo", _("To-do")),
            ("scheduled", _("Scheduled")),
        ]

    @api.model
    def _get_schedule_states(self):
        return self._set_schedule_states()

    schedule_state = fields.Selection(
        "_get_schedule_states",
        "Schedule State",
        readonly=True,
        default="waiting",
        help="Schedule State used for ordering production",
    )
    # We don't use native date_planned field because it does not have the
    # same purpose.
    schedule_date = fields.Datetime(
        help="Date at which the manufacture order is scheduled"
    )
    schedule_uid = fields.Many2one("res.users", string="Scheduled by")

    @api.multi
    def _check_planned_state(self):
        productions = self.search(
            [
                ["id", "in", self.ids],
                ["state", "=", "confirmed"],
                ["schedule_state", "!=", "waiting"],
            ]
        )
        if productions:
            production_name = []
            for production in productions:
                production_name.append(production.name)
            raise UserError(
                _(
                    "The following production order are not ready and can not "
                    "be scheduled yet : %s"
                )
                % ", ".join(production_name)
            )
        return True

    _constraints = [
        (_check_planned_state, "useless", ["schedule_state", "state"]),
    ]

    @api.multi
    def _get_values_from_selection(self, field):
        res = super(MrpProduction, self)._get_values_from_selection(field)
        if field == "schedule_state":
            # also check model name ?
            res = self._set_schedule_states()
        return res

    @api.multi
    def write(self, vals, update=True):
        if vals.get("schedule_state") == "scheduled" and not vals.get("schedule_date"):
            vals["schedule_date"] = fields.Datetime.now()
            vals["schedule_uid"] = self.env.user.id
        if vals.get("schedule_state") and vals.get("schedule_state") != "scheduled":
            vals["schedule_date"] = False
            vals["schedule_uid"] = False
        return super(MrpProduction, self).write(vals, update=update)

    @api.multi
    def set_planable_mo(self):
        """ Set the MO as to able to be manufactured 'ToDo'
            if it is ready to produce
        """
        for mo in self:
            # If MO has been scheduled when it was not ready yet (still in
            # waiting schedule_state, we can jump to schedule state already)
            if mo.schedule_date:
                mo.schedule_state = "scheduled"
            else:
                mo.schedule_state = "todo"
        return True

    @api.multi
    def action_ready(self):
        res = super(MrpProduction, self).action_ready()
        self.set_planable_mo()
        return res


class MrpProductionWorkcenterLine(models.Model):
    _inherit = ["mrp.production.workcenter.line", "abstract.selection.rotate"]
    _name = "mrp.production.workcenter.line"

    @api.model
    def __set_schedule_states(self):
        return self.env["mrp.production"]._set_schedule_states()

    schedule_state = fields.Selection(
        "__set_schedule_states",
        related="production_id.schedule_state",
        string="MO Schedule",
        select=True,
        help="'sub state' of MO state 'Ready To Produce' dedicated to "
        "planification, scheduling and ordering",
        store=True,
        readonly=True,
    )
    schedule_mo = fields.Datetime(
        related="production_id.schedule_date",
        string="Schedule MO",
        readonly=True,
        index=True,
        store=True,
    )
    #    planned_mo = fields.Datetime(
    #        related='production_id.date_planned',
    #        string='Planned MO',
    #        readonly=True,
    #        store=True)

    @api.multi
    def _iter_selection(self, direction):
        """ Allows to update the field selection to its next value
            here, we pass through the related field
            to go towards 'schedule_state' in mrp.production
        """
        for elm in self:
            elm.production_id._iter_selection(direction)
        return True

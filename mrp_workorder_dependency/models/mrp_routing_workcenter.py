from openerp import _, api, exceptions, fields, models
from openerp.osv import fields as old_fields


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    @api.model
    def _prepare_wc_line(self, bom, wc_use, level=0, factor=1):
        res = super(MrpBom, self)._prepare_wc_line(
            bom, wc_use, factor=factor, level=level
        )
        res["routing_line_id"] = wc_use.id
        return res


class MrpRoutingWorkcenter(models.Model):
    _inherit = "mrp.routing.workcenter"

    dependency_ids = fields.Many2many(
        "mrp.routing.workcenter",
        "rel_dependency_routing_worcenter",
        "routing_id",
        "routing_dependency_id",
        "Depend On",
        copy=False,
    )
    dependency_for_ids = fields.Many2many(
        "mrp.routing.workcenter",
        "rel_dependency_routing_worcenter",
        "routing_dependency_id",
        "routing_id",
        "Dependency For",
        copy=False,
    )

    @api.multi
    def write(self, vals):
        res = super(MrpRoutingWorkcenter, self).write(vals)
        if "dependency_ids" in vals:
            wos = self.env["mrp.production.workcenter.line"].search(
                [
                    ("routing_line_id", "in", self.ids),
                    ("state", "not in", ("cancel", "done")),
                ]
            )
            wos.compute_pending()
        return res

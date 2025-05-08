# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import logging

from odoo import exceptions, fields, models

logger = logging.getLogger(__name__)


class GenerateRevisionOrder(models.TransientModel):
    _name = "generate.revision.order"
    _description = "Generate hardware revision orders"

    name = fields.Char()
    bump_revision = fields.Boolean()
    planned_start_date = fields.Date()
    planned_end_date = fields.Date()

    def generate_order(self):
        revisions = self.env["product.hardware.revision"].browse(
            self.env.context.get("active_ids")
        )
        prototype_rev = revisions.filtered(lambda rec: rec.prototype)
        if prototype_rev:
            raise exceptions.UserError(
                self.env._(
                    "You can't create a ECO on a prototype revision : %s(revisions)",
                    revisions=prototype_rev.product_tmpl_id.mapped("name"),
                )
            )
        for rec in revisions:
            order = self.env["hardware.revision.order"].create(
                {
                    "name": self.name,
                    "bump_revision": self.bump_revision,
                    "hardware_revision_id": rec.id,
                    "planned_start_date": self.planned_start_date,
                    "planned_end_date": self.planned_end_date,
                }
            )

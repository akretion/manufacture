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

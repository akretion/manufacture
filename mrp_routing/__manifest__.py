# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "MRP Routing",
    "version": "14.0.1.0.0",
    "author": "Akretion,Odoo Community Association (OCA)",
    "summary": "Re-introduce the concept of routing to simplify the bom configuration",
    "category": "Manufacturing",
    "depends": [
        "mrp",
    ],
    "website": "https://github.com/OCA/manufacture",
    "data": [
        "security/ir.model.access.csv",
        "views/mrp_routing_view.xml",
        "views/mrp_routing_workcenter_view.xml",
        "views/mrp_bom_view.xml",
        "data.xml",
    ],
    "demo": [],
    "license": "AGPL-3",
    "installable": True,
}

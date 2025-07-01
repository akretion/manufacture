# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "DMR Revision Management",
    "version": "18.0.1.0.0",
    "category": "MRP",
    "license": "AGPL-3",
    "summary": "DMR Revision management",
    "author": "Akretion, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/manufacture",
    "depends": ["mrp", "purchase", "mrp_subcontracting", "mrp_hardware_revision"],
    "data": [
        "security/ir.model.access.csv",
        "views/engineering_change_order.xml",
        "views/dmr_revision.xml",
        "views/dmr.xml",
        "views/purchase_order.xml",
        "views/stock_lot.xml",
        "views/mrp_production.xml",
    ],
    "demo": [],
    "installable": True,
}

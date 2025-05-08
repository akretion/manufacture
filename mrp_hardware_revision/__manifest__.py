# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Hardware Revision Management",
    "version": "18.0.1.0.0",
    "category": "MRP",
    "license": "AGPL-3",
    "summary": "Hardware revision management",
    "author": "Akretion, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/manufacture",
    # first shot make one main module / split later
    "depends": ["mrp", "purchase", "mrp_subcontracting"],
    "data": [
        "security/ir.model.access.csv",
        "views/hardware_revision_menu.xml",
        "views/hardware_revision_order.xml",
        "views/product_hardware_revision.xml",
        "views/purchase_order.xml",
        "views/stock_quant.xml",
        "views/stock_lot.xml",
        "views/mrp_production.xml",
        "wizards/generate_revision_order.xml",
    ],
    "demo": [],
    "installable": True,
}

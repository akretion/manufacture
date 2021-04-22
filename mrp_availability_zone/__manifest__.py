# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "MRP Availability",
    "version": "14.0.1.0.0",
    "author": "Akretion,Odoo Community Association (OCA)",
    "summary": "Consider raw material availability on a bigger zone than where it is "
    "consumed",
    "category": "Manufacturing",
    "depends": [
        "mrp",
        "queue_job",
        "stock_available_immediately",
    ],
    "website": "https://github.com/OCA/manufacture",
    "data": ["views/mrp_production_view.xml"],
    "demo": [],
    "license": "AGPL-3",
    "installable": True,
}

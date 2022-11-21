# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "MRP Load By Schedule State",
    "summary": "Adds load information on workcenter by mo schedule state",
    "version": "16.0.1.0.0",
    "category": "Manufacturing",
    "website": "https://github.com/OCA/manufacture",
    "author": "Akretion,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "mrp_schedule_state",
    ],
    "data": [
        "views/mrp_workcenter.xml",
    ],
}

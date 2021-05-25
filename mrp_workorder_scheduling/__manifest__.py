# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "MRP Workorder Scheduling",
    "version": "14.0.1.0.0",
    "author": "Akretion,Odoo Community Association (OCA)",
    "summary": "Order workorders inside a workcenter",
    "category": "Manufacturing",
    "depends": [
        "mrp_schedule_state",
        "mrp_workcenter_workorder_link",
    ],
    "website": "https://github.com/OCA/manufacture",
    "data": [
        "security/ir.model.access.csv",
        "views/mrp_workcenter_order_key_views.xml",
        "views/mrp_workcenter_view.xml",
    ],
    "demo": [
        "demo/mrp_workcenter_ordering_key.xml",
    ],
    "license": "AGPL-3",
    "installable": True,
}

# Copyright 2016 Antiun Ingenieria S.L. - Javier Iniesta
# Copyright 2019 Rubén Bravo <rubenred18@gmail.com>
# Copyright 2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "MRP Sale Info",
    "summary": "Adds sale information to Manufacturing models",
    "version": "16.0.1.1.0",
    "category": "Manufacturing",
    "website": "https://github.com/OCA/manufacture",
    "author": "Akretion, Odoo Community Association (OCA)",
    "maintainers": ["florian-dacosta"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "mrp",
    ],
    "data": [
        "views/mrp_bom.xml",
    ],
}

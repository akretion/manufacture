from odoo import api, fields, models


class InputMixin(models.AbstractModel):
    _name = "input.mixin"
    _description = "Input Configuration mixin"

    test_config = fields.Boolean(default=False, required=True)

    def configure(self):
        # TODO: remove
        for rec in self:
            for line in rec.bom_id.bom_line_ids:
                product = line.product_id
                if product.dia_tube and product.dia_tube != rec.dia_tube:
                    line.unselected = True
                else:
                    line.unselected = False

    @api.depends("manoeuvre")
    def _compute_protocol(self):
        for rec in self:
            if rec.manoeuvre != "moteur":
                rec.protocol = False

class InputConfig(models.Model):
    _name = "input.config"
    _inherit = ["input.config", "input.mixin"]

CONFIG_ELEMENTS = ("test_config")

class InputLine(models.Model):
    _name = "input.line"
    _inherit = ["input.line", "input.mixin"]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("config_id"):
                config = self.env["input.config"].browse(vals["config_id"])
                if not vals.get("manoeuvre"):
                    vals["protocol"] = config.protocol
                    vals["manoeuvre"] = config.manoeuvre
                for element in CONFIG_ELEMENTS:
                    if not vals.get(element):
                        vals[element] = config[element]
        return super().create(vals_list)

    def ui_configure(self):
        self.ensure_one()
        # TODO
        lines, data, elements = [], [], dict()
        for elm in CONFIG_ELEMENTS:
            if self._fields[elm].type == "many2one":
                value = self[elm].display_name
            else:
                value = self[elm]
            elements[elm] = value

        bom = self.bom_id
        content = bom.check_domain(elements)
        self.env["mrp.bom"].create({
                "product_tmpl_id": bom.product_tmpl_id.id,
                "product_id": bom.product_id.id,
                "product_qty": self.count,
                "product_uom_id": bom.product_uom_id.id,
                "bom_line_ids": [
                    (0, 0, {
                        "product_id": line.product_id.id,
                        "product_qty": self.count * line.product_qty,
                        "product_uom_id": line.product_uom_id.id
                    })
                    for line in content
                ],
            })

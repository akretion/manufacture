from odoo import fields, models


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    configuration_type = fields.Selection(
        selection=[
            ("variable", "Variable BOM"),
            ("configured", "BOM from variable BOM"),
            ("normal", "Normal BOM"),
        ],
        default="normal",
        required=True,
    )

    def _compute_data_from_line_and_quantity(self, line, line_quantity):
        return {
            "product_tmpl_id": line.product_tmpl_id,
            "product_id": line.product_id,
            "product_qty": line_quantity,
            "product_uom_id": line.product_uom_id,
        }

    @classmethod
    def _get_bom_domain_for_config(cls):
        "You may override me"
        return [("configuration_type", "=", "variable")]

    def find_parent_bom_in_exploded(self, boms_done, parent_bom_id):
        parent_bom_data = False
        for bom, bom_data in boms_done:
            if bom.id == parent_bom_id.id:
                parent_bom_data = bom_data
        return parent_bom_data

    def _compute_line_qty(self, line_data, bom_line, input_line):
        qty = line_data["qty"]

        if bom_line.use_formula_compute_qty:
            qty = line_data["qty"] * bom_line.compute_qty_from_formula(input_line)

        return qty

    def _recompute_line_data_quantity(self, input_line, boms_done, bom_line, line_data):
        """This recompute the line data quantity during explode after"""
        parent_line = line_data["parent_line"]

        line_data["qty"] = self._compute_line_qty(line_data, bom_line, input_line)

        while parent_line and parent_line.bom_id.type == "phantom":
            parent_bom_data = False
            for bom, bom_data in boms_done:
                if bom.id == parent_line.bom_id.id:
                    parent_bom_data = bom_data
            if parent_bom_data:
                line_data["parent_line"] = parent_bom_data["parent_line"]
                parent_line = line_data["parent_line"]
            else:
                break

    def _recompute_variable_quantity(self, quantity, input_line, boms_done, lines_done):
        """This compute the quantity for components which have a parent that is computed
        from formula"""
        for _, bom_data in boms_done:
            if (
                bom_data["parent_line"]
                and bom_data["parent_line"].use_formula_compute_qty
            ):
                bom_data["qty"] = bom_data["original_qty"] * bom_data[
                    "parent_line"
                ].compute_qty_from_formula(input_line)

        for bom_line, line_data in lines_done:
            self._recompute_line_data_quantity(
                input_line, boms_done, bom_line, line_data
            )

    def explode(
        self, product, quantity, picking_type=False, never_attribute_values=False
    ):
        boms_done, lines_done = super().explode(
            product, quantity, picking_type, never_attribute_values
        )
        input_line_id = self.env.context.get("input_line_id", False)
        if input_line_id:
            input_line = self.env["input.line"].browse(input_line_id)
            self._recompute_variable_quantity(
                quantity, input_line, boms_done, lines_done
            )
        return boms_done, lines_done

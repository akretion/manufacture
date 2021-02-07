# Copyright 2020 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
import odoo.addons.decimal_precision as dp


class QcInspectionLineWizard(models.TransientModel):
    _name = "qc.inspection.line.wizard"
    _description = "Module description"

    qc_inspection_id = fields.Many2one(comodel_name="qc.inspection")
    qc_insp_line_id = fields.Many2one(
        string="Inspection Line", comodel_name="qc.inspection.line", readonly=True,
    )
    line_index = fields.Integer()
    is_last_line = fields.Boolean()

    question_type = fields.Selection(related="qc_insp_line_id.question_type")

    possible_ql_values = fields.Many2many(related="qc_insp_line_id.possible_ql_values")
    qualitative_value = fields.Many2one(
        comodel_name="qc.test.question.value",
        string="Qualitative value",
        help="Value of the result for a qualitative question.",
        domain="[('id', 'in', possible_ql_values)]",
    )

    valid_values = fields.Char(related="qc_insp_line_id.valid_values")
    quantitative_value = fields.Float(
        "Quantitative value",
        digits=dp.get_precision("Quality Control"),
        help="Value of the result for a quantitative question.",
    )

    def _write_vals_on_insp_line(self, quant_val, qual_val):
        self.qc_insp_line_id.write(
            {"quantitative_value": quant_val, "qualitative_value": qual_val.id}
        )

    def action_next_line(self):
        self.ensure_one()
        insp_line_wiz_view_xmlid = "quality_control.qc_inspection_line_wizard_view_form"
        qc_insp_id = self.qc_inspection_id
        qc_line_ids = qc_insp_id.inspection_lines
        next_index = self.line_index + 1

        self._write_vals_on_insp_line(self.quantitative_value, self.qualitative_value)

        return {
            "name": _("Inspection Question"),
            "context": {
                "default_qc_inspection_id": qc_insp_id.id,
                "default_qc_insp_line_id": qc_line_ids[next_index].id,
                "default_line_index": next_index,
                "default_is_last_line": next_index + 1 == len(qc_line_ids),
            },
            "view_id": self.env.ref(insp_line_wiz_view_xmlid).id,
            "res_model": "qc.inspection.line.wizard",
            "view_type": "form",
            "view_mode": "form",
            "type": "ir.actions.act_window",
            "target": "new",
        }

    def action_end(self):
        self._write_vals_on_insp_line(self.quantitative_value, self.qualitative_value)

        # FIXME: This action creates a new qc.inspection view, adding an unnecessary
        # element on the breadcrumb
        action = self.env.ref("quality_control.action_qc_inspection").read()[0]
        action.update({"res_id": self.qc_inspection_id.id, "views": [(False, "form")]})
        return action

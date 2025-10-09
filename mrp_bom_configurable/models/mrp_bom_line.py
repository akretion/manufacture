from ast import operator
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval, wrap_module

logger = logging.getLogger(__name__)


def check_domain(domain, values, current_name, parent_name):
    if domain is None or not isinstance(domain, str):
        return True

    domain = domain.replace("'", '"')
    domain = domain.replace('"="', '"=="')
    domain = domain.replace('"ilike"', '"in"')
    domain = safe_eval(domain.replace("!==", "!="))

    if len(domain) == 0:
        return True

    if len(domain) == 1:
        domain.append(True)

    # check that there is the proper amount of operator
    # and operand
    operator_count = 0
    operand_count = 0
    for el in domain:
        if el in ["&", "|"]:
            operator_count += 1
        else:
            operand_count += 1

    if operand_count != operator_count + 1:
        # there is an imbalance between operator and operand
        # fix it and make domain a proper PN input
        # a = [o, d, d, d, d, o, d, d]
        # a = [o, d, d, d, o, d, o, d, d]
        # a = [o, d, d, o, d, o, d, o, d, d]
        # a = [o, d, d, o, d, o, d, o, d, d]
        # a = [o, d, o, d, o, d, o, d, o, d, d]
        current_index = len(domain) - 2
        while current_index > 0:
            if domain[current_index - 1] not in ["&", "|"]:
                domain.insert(current_index, "&")
                current_index += 1
            current_index -= 2

    # This check the front of the domain which should always be a operator
    if domain[0] not in ["&", "|"]:
        domain.insert(0, "&")

    # We reverse to evaluate the domain using RPN
    rpn_domain = reversed(domain)

    operand_stack = []

    for token in rpn_domain:
        if token == "&" or token == "|":
            op_b = operand_stack.pop()
            op_a = operand_stack.pop()
            result = evaluate_operator(
                token, op_b, op_a, values, current_name, parent_name
            )
            operand_stack.append(result)
        else:
            operand_stack.append(token)

    return operand_stack.pop()


def evaluate_domain_operand(domain, values, current_name, parent_name):
    if isinstance(domain, bool):
        return domain
    else:
        values["line_data"] = {"name": current_name}

        param, operator, value = domain

        # if param not in values:
        #     raise UserError(
        #         f"Wrong param name ({param}) for domain {current_name}"
        #         + f"in {parent_name}"
        #     )
        if operator == "in":
            code = f"{repr(value)} {operator} {param}"
        else:
            code = f"{param} {operator} {repr(value)}"

        try:
            return safe_eval(code, values)
        except SyntaxError as e:
            raise ValidationError(
                f"Domain {domain} is incorrect on {current_name}"
            ) from e


def evaluate_operator(operator, a, b, values, current_name, parent_name):
    if operator == "&":
        return evaluate_domain_operand(
            a, values, current_name, parent_name
        ) & evaluate_domain_operand(b, values, current_name, parent_name)
    if operator == "|":
        return evaluate_domain_operand(
            a, values, current_name, parent_name
        ) | evaluate_domain_operand(b, values, current_name, parent_name)


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    domain = fields.Text(help="Odoo syntax domain only")
    use_formula_compute_qty = fields.Boolean(
        string="Use formula to compute qty", default=False, required=False
    )
    qty_formula = fields.Text(
        string="Quantity formula", help="Formula to compute", default="result = qty"
    )
    condition = fields.Text(help="Comment explaining domain if needed")

    def _create_formula_eval_context(self, input_line):
        context = {
            "qty": self.product_qty,
        }
        params = input_line._get_config_elements()

        for param in params:
            if not input_line._fields[param].relational:
                context[param] = input_line[param]
            elif hasattr(input_line[param], "value") or hasattr(
                input_line[param], "name"
            ):
                context[param] = input_line[param]
        math_module = __import__("math")
        math = wrap_module(
            math_module, [f for f in math_module.__dict__ if "__" not in f]
        )
        context["math"] = math
        return context

    def _run_formula(self, eval_context):
        safe_eval(self.qty_formula.strip(), eval_context, mode="exec", nocopy=True)

    def compute_qty_from_formula(self, input_line):
        eval_context = self._create_formula_eval_context(input_line)
        self._run_formula(eval_context)
        return eval_context.get("result", self.product_qty)

    def check_domain(self, values):
        self.ensure_one()
        if not self.domain:
            return True
        else:
            return check_domain(
                self.domain, values, self.product_id.name, self.bom_id.product_id.name
            )

    def _should_not_be_included_in_bom(self, input_line):
        return not self.check_domain(input_line._get_input_line_values())

    def _skip_bom_line(self, product, never_attribute_values=False):
        self.ensure_one()
        res = super()._skip_bom_line(product, never_attribute_values)

        input_line_id = self.env.context.get("input_line_id", False)
        if input_line_id:
            input_line = self.env["input.line"].browse(input_line_id)
            if input_line:
                return self._should_not_be_included_in_bom(input_line)

        return res

    def ui_update_domain(self):
        self.ensure_one()
        return {
            "name": _(f"Domain for {self.product_id}"),
            "type": "ir.actions.act_window",
            "res_model": "mrp.bom.line",
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
        }

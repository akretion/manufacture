# coding: utf-8
# © 2017 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import _, models, api, fields


class QuickAddComponent(models.TransientModel):
    _name = "quick.add.component"

    product_qty = fields.Float(
        required=True, default='1.0')
    product_tmpl_ids = fields.Many2many(
        comodel_name='product.template', string='Products', required=True)
    product_ids = fields.Many2many(
        comodel_name='product.product', string='Components', required=True)

    @api.model
    def default_get(self, fields):
        res = super(QuickAddComponent, self).default_get(fields)
        product_tmpl_ids = self.env.context.get('active_ids')
        if product_tmpl_ids:
            res['product_tmpl_ids'] = product_tmpl_ids
        return res

    @api.multi
    def apply(self):
        self.ensure_one()
        self.product_tmpl_ids.write({
            'bom_line_ids': [(0, 0, {
                'product_qty': self.product_qty,
                'product_id': x.id}) for x in self.product_ids]})
        if len(self.product_tmpl_ids._ids) == 1:
            return
        domain = [('id', 'in', self.product_tmpl_ids._ids)]
        return {
            'name': _("Products with updated boms"),
            'type': 'ir.actions.act_window',
            'res_id': self.env.ref('product.product_normal_action').id,
            'view_mode': 'tree,form',
            'domain': domain,
            'res_model': 'product.template',
        }

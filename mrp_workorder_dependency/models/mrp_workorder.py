
from openerp import fields, models, api, exceptions, _
from openerp.osv import fields as old_fields


class MrpProductionWorkcenterLine(models.Model):
    _inherit = 'mrp.production.workcenter.line'

    @api.multi
    def compute_pending(self):
        pendings = self.browse(False)
        not_pendings = self.browse(False)
        for line in self:
            for depend_line in line.dependency_ids:
                if depend_line.state != 'done':
                    pendings |= line
                    break
            else:
                not_pendings |= line
        if pendings:
            pendings.write({'pending': True})
        if not_pendings:
            not_pendings.write({'pending': False})

    @api.multi
    def _get_dependency_ids(self):
        for line in self:
            if line.routing_line_id.dependency_ids:
                routing_line_ids = line.routing_line_id.dependency_ids.ids
                depend_lines = self.search([
                    ['production_id', '=', line.production_id.id],
                    ['routing_line_id', 'in', routing_line_ids],
                    ])
                line.dependency_ids = [(6 ,0, depend_lines.ids)] 

    @api.multi
    def _get_dependency_for_ids(self):
        for line in self:
            if line.routing_line_id.dependency_for_ids:
                routing_line_ids = line.routing_line_id.dependency_for_ids.ids
                depend_lines = self.search([
                    ['production_id', '=', line.production_id.id],
                    ['routing_line_id', 'in', routing_line_ids],
                    ])
                line.dependency_for_ids = [(6 ,0, depend_lines.ids)]

#    @api.multi
#    @api.depends('dependency_ids.state', 'dependency_ids.routing_line_id')
#    def _is_pending(self):
#        print 'll', self
#        for line in self:
#            result[line.id] = False
#            for depend_line in line.dependency_ids:
#                if depend_line.state != 'done':
#                    line.pending = True
#                    break


    # Avoid compute field because we do not want to recompute it for done/cancel
    # wos in case of change in routing line...
    # also, it seems complicated depending on the not stored m2m fields.
    pending = fields.Boolean()
#        '_is_pending',
#        store=True)

    routing_line_id = fields.Many2one(
        'mrp.routing.workcenter',
        'Routing Line',
        index=True)

    dependency_ids = fields.Many2many(
        compute='_get_dependency_ids',
        comodel_name='mrp.production.workcenter.line',
        string='Dependency')
    dependency_for_ids = fields.Many2many(
        compute='_get_dependency_for_ids',
        comodel_name='mrp.production.workcenter.line',
        string='Dependency for')

    @api.model
    def create(self, vals):
        wo = super(MrpProductionWorkcenterLine, self).create(vals)
        (wo + wo.dependency_for_ids).compute_pending()
        return wo

    @api.multi
    def write(self, vals, update=True):
        if vals.get('state') in ('done', 'startworking') and (not 'pending' in vals or vals.get('pending')):
            pending_wos = self.filtered(lambda w: w.pending)
            if pending_wos:
                raise exceptions.UserError(
                    _('Impossible to start or end a pending workorder.'
                      ' (%s)' % pending_wos.ids))
        res = super(MrpProductionWorkcenterLine, self).write(vals, update=update)
        if vals.get('state', '') in ('done', 'cancel') or 'routing_line_id' in vals:
            self.mapped('dependency_for_ids').compute_pending()
        return res

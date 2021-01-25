# Copyright 2018 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date
from odoo import api, fields, models, SUPERUSER_ID, _

import logging
_logger = logging.getLogger(__name__)


class CustomerOutstandingStatementWizard(models.TransientModel):
    """Customer Outstanding Statement wizard."""

    _name = 'customer.outstanding.statement.wizard'
    _description = 'Customer Outstanding Statement Wizard'

    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id,
        string='Company'
    )

    date_end = fields.Date(required=True,
                           default=fields.Date.to_string(date.today()))
    show_aging_buckets = fields.Boolean(string='Include Aging Buckets',
                                        default=True)
    number_partner_ids = fields.Integer(
        default=lambda self: len(self._context['active_ids'])
    )
    filter_partners_non_due = fields.Boolean(
        string='Don\'t show partners with no due entries', default=True)
    account_type = fields.Selection(
        [('receivable', 'Receivable'),
         ('payable', 'Payable')], string='Account type', default='receivable')
    use_detailed = fields.Boolean('More information', default=True)
    show_lines = fields.Boolean('Show lines', help='If checked in letter will be show detailed report, if not show '
                                                   'only total amount', default=True)
    use_partner_selection = fields.Selection([
        ('shipping', _('Show shipping address')),
        ('contact', _('Show partner contact')),
        ('both', _('Show both')),], 'Show partner details')
    use_invoice_detail = fields.Boolean('Invoice information')
    use_sale_detail = fields.Boolean('Sale order information')
    use_picking_detail = fields.Boolean('Stock picking information')

    print_sets = fields.Boolean("Ungroup by sets")
    print_lots = fields.Boolean("Print Lots")

    use_product_properties = fields.Selection([
        ('description', _('Use descriptions')),
        ('properties', _('Use properties')),],
        string="Type product description",
        help='Choice type of the view for product description',
        default="description")
    print_properties = fields.One2many('product.properties.print.wizard', 'outstanding_id', 'Print properties')
    product_prop_static_id = fields.Many2one("product.properties.static", 'Static Product properties')
    static_template_id = fields.Many2one('base.comment.template', 'Comment Template', related="product_prop_static_id.comment_template_id",
                                          domain="[('position', '=', 'prints')]", store=True)
    static_note = fields.Html(string='Comment summary', related="product_prop_static_id.comment_template_id.text", store=True)
    issue_user_id = fields.Many2one("hr.employee", related="product_prop_static_id.issue_user_id", store=True)
    use_digital_sign = fields.Boolean('Use digital signature')
    represent_user_ids = fields.One2many('hr.employee', string='Represent employees', compute="_compute_represent_user_ids")

    category_print_properties = fields.Many2one('product.properties.print.category', 'Default Print properties category')
    use_partner = fields.Boolean('Use partner properties')
    empty_properties = fields.Boolean('Remove all old properties')

    @api.multi
    def _compute_represent_user_ids(self):
        user = self.env.user
        for wiz in self:
            wiz.represent_user_ids = False
            if user.id == SUPERUSER_ID:
                users = self.env['hr.employee'].search([])
                wiz.represent_user_ids = users
            else:
                users = user.employee_ids
                for represent in users:
                    for represented in represent.mapped('replacement_employee_ids'):
                        wiz.represent_user_ids |= represented
            # wiz.write({})
            # _logger.info("USERS %s" % wiz.represent_user_ids)

    # @api.onchange
    # def _onchange_product_prop_static_id(self):
    #     for record in self:
    #         record._compute_represent_user_ids()

    @api.onchange('category_print_properties', 'use_partner', 'empty_properties')
    def _onchange_category_print_properties(self):
        for record in self:
            if record.category_print_properties:
                record.print_properties = self.env['product.properties.print.wizard'].set_all_print_properties(record, False, ['category'])
            if record.use_partner:
                record.print_properties = self.env['product.properties.print.wizard'].set_all_print_properties(record, False, ['partner'])
            if record.empty_properties:
                record.print_properties = False

    @api.onchange('static_template_id')
    def _onchange_static_template_id(self):
        self.ensure_one()
        if self.static_template_id and self.static_template_id.use:
            property_data_id = self.env['product.properties.static'].create({'comment_template_id': self.static_template_id.id})
            self.product_prop_static_id = property_data_id
            #vals = self.env['product.properties.static'].static_property_data(self, {}, property_data={'comment_template_id': self.static_template_id.id})
            #_logger.info("VALS %s:%s:%s" % (property_data_id, self.product_prop_static_id, self.static_template_id))
            self.static_note = self.static_template_id.get_value(field_name='text')

    @api.multi
    def button_export_pdf(self):
        self.ensure_one()
        return self._export()

    def _prepare_outstanding_statement(self):
        self.ensure_one()
        self.product_prop_static_id.write({'object_id': "%s,%d" % ("%s" % self._name, self.id)})
        return {
            'date_end': self.date_end,
            'company_id': self.company_id and self.company_id.id or False,
            'partner_ids': self._context['active_ids'],
            'show_aging_buckets': self.show_aging_buckets,
            'filter_non_due_partners': self.filter_partners_non_due,
            'account_type': self.account_type,
            'use_detailed': self.use_detailed,
            'use_sale_detail': self.use_sale_detail,
            'use_partner_selection': self.use_partner_selection,
            'use_invoice_detail': self.use_invoice_detail,
            'use_picking_detail': self.use_picking_detail,
            'use_product_properties': self.use_product_properties,
            'static_note': self.static_note,
            'static_template_id': self.static_template_id and self.static_template_id.get_value(field_name='short') or False,
            'product_prop_static_id': self.product_prop_static_id and self.product_prop_static_id.id or False,
            'print_properties': self.print_properties.ids,
            'print_sets': self.print_sets,
            'print_lots': self.print_lots,
            'show_lines': self.show_lines,
            'use_digital_sign': self.use_digital_sign,
            'issue_user_id': self.issue_user_id and self.issue_user_id.id or False,
        }

    def _export(self):
        """Export to PDF."""
        data = self._prepare_outstanding_statement()
        return self.env.ref(
            'customer_outstanding_statement'
            '.action_print_customer_outstanding_statement').report_action(
            self, data=data)

    @api.model_cr
    def _transient_clean_rows_older_than(self, seconds):
        assert self._transient, "Model %s is not transient, it cannot be vacuumed!" % self._name
        # Never delete rows used in last 5 minutes
        seconds = max(seconds, 300)
        query = ("SELECT id FROM " + self._table + " WHERE"
            " COALESCE(write_date, create_date, (now() at time zone 'UTC'))::timestamp"
            " < ((now() at time zone 'UTC') - interval %s)")
        self._cr.execute(query, ("%s seconds" % seconds,))
        ids = [x[0] for x in self._cr.fetchall()]
        # Remove before it the rows in product.properties.print
        if self._table == 'customer.outstanding.statement.wizard':
            for line in self.sudo().browse(ids):
                print_properties = self.env['product.properties.static'].searsh([('object_id', '=', '%s,%s' % (self._name, line.id))])
            if print_properties:
                print_properties.unlink()
        self.sudo().browse(ids).unlink()

    @api.model
    def default_get(self, fieldss):
        res = super(CustomerOutstandingStatementWizard, self).default_get(fieldss)
        user = self.env.user
        ids = []
        if user.id == SUPERUSER_ID:
            users = self.env['hr.employee'].search([])
            ids = [x.id for x in users]
        else:
            users = user.employee_ids
            for represent in users:
                for represented in represent.mapped('replacement_employee_ids'):
                    ids.append(represented.id)
        res.update({
            'company_id': self.env.user.company_id.id,
            'date_end': fields.Date.today(),
            'show_aging_buckets': True,
            'number_partner_ids': len(self._context['active_ids']),
            'filter_partners_non_due': True,
            'account_type': 'receivable',
            'use_detailed': True,
            'show_lines': True,
            'use_product_properties': 'description',
            'represent_user_ids': [(6, False, ids)],
        })
        return res


class ProductPropertiesPrintWizard(models.TransientModel):
    _name = "product.properties.print.wizard"
    _description = "Product properties for printing wizard"
    _order = "system_properties, sequence"

    def _get_field_name_filter(self):
        static_properties_obj = self.env['product.properties.static']
        ret = []
        for g in filter(lambda r: r not in static_properties_obj.ignore_fields(), static_properties_obj._fields):
            field = static_properties_obj.fields_get(g)[g]
            ret.append((g, field['string']))
        return ret

    name = fields.Many2one("product.properties.type", string="Property name",  translate=True)
    print = fields.Boolean('Print')
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'product.properties.print'))
    outstanding_id = fields.Many2one("customer.outstanding.statement.wizard", "Statement wizard")
    sequence = fields.Integer("Sequence", default=1, help="The first in the sequence is the default one.")
    system_properties = fields.Boolean('System used')
    static_field = fields.Selection(selection="_get_field_name_filter", string="Static Properties Field name")

    def get_print_properties(self):
        return [x.name.id for x in self if not x.static_field and x.print]

    def get_print_static_properties(self):
        return [x.static_field for x in self if x.static_field and x.print]

    def set_all_print_properties(self, res, lines, mode=['standard']):
        def add_exluded(x, ids):
            ids.update([x])
            return x

        mode = self._context.get('mode_print_properties') and self._context['mode_print_properties'] or mode
        #_logger.info("MODE %s:%s:%s" % (self._context, mode, 'partner_id' in res._fields))

        if res._name == 'customer.outstanding.statement.wizard':
            res_model_id = 'outstanding_id'
        else:
            return False
        for record in res:
            static_properties_obj = self.env['product.properties.static']
            print_properties = []
            ids = set([])
            print_ids = False
            partner_print_ids = False
            default_print_ids = False
            print_static_ids = False

            if 'category' in mode and 'category_print_properties' in res._fields:
                print_static_ids = [x.static_field for x in record.category_print_properties.mapped('type_ids') if not x.type_id and x.static_field]
                default_print_ids = [x for x in record.category_print_properties.mapped('type_ids') if x.type_id and not x.static_field]
                for line in record.category_print_properties.mapped('type_ids').filtered(lambda x: not x.type_id and x.static_field in self.env['product.properties.static']._set_static_ignore_print_properties()):
                    setattr(record.category_print_properties, 'invoice_sub_type', getattr(line, 'invoice_sub_type'))
            if 'partner' in mode and 'partner_id' in res._fields:
                partner_print_ids = [x for x in record.partner_id.print_properties if x.print]
                #_logger.info("PARTNER %s:%s" % (partner_print_ids, record.partner_id))
            if 'standard' in mode:
                print_static_ids = filter(lambda r: r not in static_properties_obj.ignore_fields(),
                                          static_properties_obj._fields)
                for r in lines.mapped('product_id'):
                    if not print_ids:
                        print_ids = r.product_properties_ids | r.tproduct_properties_ids
                    else:
                        print_ids |= r.product_properties_ids | r.tproduct_properties_ids
            if (print_ids or print_static_ids or partner_print_ids or default_print_ids) and not record.print_properties:
                if default_print_ids:
                    print_properties += [(0, False, {'name': add_exluded(x.type_id.id, ids), res_model_id: res.id, 'print': True, 'sequence': x.sequence}) for x in default_print_ids if x.type_id and x.type_id.id not in list(ids)]
                if partner_print_ids:
                    print_properties += [(0, False, {'name': add_exluded(x.name.id, ids), res_model_id: res.id, 'print': True, 'sequence': x.sequence}) for x in partner_print_ids if x.name and x.name.id not in list(ids) and not x.static_field]
                    print_properties += [(0, False, {'static_field': x.static_field, res_model_id: res.id, 'print': True, 'sequence': 9999}) for x in partner_print_ids if not x.name and x.static_field and x.static_field not in static_properties_obj.ignore_fields()]
                if print_ids:
                    print_properties += [(0, False, {'name': add_exluded(x.name.id, ids), res_model_id: res.id, 'print': True, 'sequence': x.sequence}) for x in print_ids if x.name and x.name.id not in list(ids)]
                if print_static_ids:
                    print_properties += [(0, False, {'static_field': x, res_model_id: res.id, 'print': True, 'sequence': 9999}) for x in print_static_ids]
                #_logger.info("LIST %s:%s:%s:%s" % (self._context.get('mode_print_properties'), lines.mapped('product_id'), print_properties, ids))
            return print_properties
        return False


#class ProductPropertiesPrint(models.Model):
#    _inherit = "product.properties.print"
#
#    outstanding_id = fields.Many2one("customer.outstanding.statement.wizard", string="Invoice", index=True)
